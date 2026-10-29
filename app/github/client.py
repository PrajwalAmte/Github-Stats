import itertools
import logging
import time

import httpx

from app.config import settings
from app.exceptions import (
    GithubApiError,
    GithubAuthenticationError,
    GithubNotFoundError,
    GithubRateLimitError,
)
from app.github.models import GithubUser, RepositoryConnection
from app.github.queries import REPOS_PAGE_QUERY, USER_QUERY

logger = logging.getLogger(__name__)

# Round-robin start position shared across requests, so load spreads
# over every configured token instead of draining the first one.
_token_cycle = itertools.count()


class GithubClient:
    """GitHub GraphQL API client.

    Opens a fresh connection pool per fetch rather than holding one on
    the instance: serverless runtimes may back each invocation with a
    different event loop, and a pooled client bound to a dead loop is
    exactly the kind of intermittent failure this service exists to
    avoid.
    """

    def __init__(self, tokens: list[str] | None = None, api_url: str | None = None):
        self.tokens = tokens if tokens is not None else settings.github_tokens
        self.api_url = api_url or settings.github_api_url

    async def fetch_user(self, login: str) -> GithubUser:
        """Fetch profile, contribution calendar and repositories (with
        languages) for a user. Paginates repos up to settings.max_repo_pages."""
        if not self.tokens:
            raise GithubAuthenticationError("GITHUB_TOKEN is not configured")

        timeout = httpx.Timeout(settings.github_timeout_seconds, connect=3.0)
        async with httpx.AsyncClient(timeout=timeout) as http:
            started = page_started = time.monotonic()
            data = await self._execute(http, USER_QUERY, {"login": login})
            if not data.get("user"):
                raise GithubNotFoundError(f"User {login} not found")

            user = GithubUser(**data["user"])

            pages = 1
            page_info = user.repositories.page_info
            while page_info.has_next_page and pages < settings.max_repo_pages:
                now = time.monotonic()
                # Assume the next page takes as long as the last one.
                if (now - started) + (now - page_started) > settings.github_soft_budget_seconds:
                    break
                page_started = now
                data = await self._execute(
                    http, REPOS_PAGE_QUERY, {"login": login, "cursor": page_info.end_cursor}
                )
                page = RepositoryConnection(**data["user"]["repositories"])
                user.repositories.nodes.extend(page.nodes)
                page_info = page.page_info
                pages += 1

            if page_info.has_next_page:
                logger.info(
                    f"{login} has {user.repositories.total_count} repos; "
                    f"using the top {len(user.repositories.nodes)} by stars"
                )

        return user

    async def _execute(self, http: httpx.AsyncClient, query: str, variables: dict) -> dict:
        """Run a query, rotating through tokens on rate-limit/auth failures."""
        start = next(_token_cycle)
        last_error: GithubApiError | None = None

        for i in range(len(self.tokens)):
            token = self.tokens[(start + i) % len(self.tokens)]
            try:
                return await self._execute_with_token(http, token, query, variables)
            except (GithubRateLimitError, GithubAuthenticationError) as e:
                logger.warning(f"Token #{(start + i) % len(self.tokens)} unusable: {e}")
                last_error = e

        assert last_error is not None
        raise last_error

    async def _execute_with_token(
        self, http: httpx.AsyncClient, token: str, query: str, variables: dict
    ) -> dict:
        try:
            response = await http.post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers={"Authorization": f"Bearer {token}"},
            )
        except httpx.HTTPError as e:
            raise GithubApiError(f"GitHub request failed: {type(e).__name__}") from e

        if response.status_code == 401:
            raise GithubAuthenticationError("GitHub authentication failed")
        if response.status_code in (403, 429):
            raise GithubRateLimitError("GitHub API rate limit exceeded")
        if response.status_code >= 400:
            raise GithubApiError(f"GitHub API error: {response.status_code}")

        payload = response.json()
        errors = payload.get("errors") or []
        if errors:
            error = errors[0]
            if error.get("type") == "RATE_LIMITED":
                raise GithubRateLimitError(error.get("message", "rate limited"))
            if error.get("type") == "NOT_FOUND":
                raise GithubNotFoundError(error.get("message", "not found"))
            # Partial data with errors (e.g. one inaccessible repo) is
            # still usable — only fail if nothing came back.
            if not payload.get("data"):
                raise GithubApiError(f"GraphQL error: {error.get('message', 'unknown')}")

        return payload.get("data") or {}
