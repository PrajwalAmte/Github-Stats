import logging

import httpx

from app.config import settings
from app.exceptions import (
    GithubApiError,
    GithubAuthenticationError,
    GithubNotFoundError,
    GithubRateLimitError,
)
from app.github.models import GithubRepository, GithubUserResponse, RepositoryLanguages
from app.github.queries import (
    PAGINATED_REPOS_QUERY,
    REPO_LANGUAGES_QUERY,
    USER_QUERY,
)

logger = logging.getLogger(__name__)


class GithubClient:
    """GitHub GraphQL API client."""

    def __init__(self, token: str | None = None, api_url: str | None = None):
        self.token = token or settings.github_token
        self.api_url = api_url or settings.github_api_url
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def _execute_query(self, query: str, variables: dict) -> dict:
        """Execute a GraphQL query."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                self.api_url,
                json={"query": query, "variables": variables},
                headers=self.headers,
            )

            if response.status_code == 401:
                raise GithubAuthenticationError("GitHub authentication failed")
            if response.status_code == 403:
                raise GithubRateLimitError("GitHub API rate limit exceeded")
            if response.status_code >= 500:
                raise GithubApiError(f"GitHub API server error: {response.status_code}")

            data = response.json()

            if "errors" in data:
                error_msg = data["errors"][0].get("message", "Unknown error")
                if "Could not resolve" in error_msg:
                    raise GithubNotFoundError(f"User not found: {error_msg}")
                raise GithubApiError(f"GraphQL error: {error_msg}")

            return data.get("data", {})

    async def fetch_user_data(self, username: str) -> GithubUserResponse:
        """
        Fetch complete user data including profile, contributions, and repositories.
        Automatically handles pagination if user has >100 repos.
        """
        # Initial query with first 100 repos
        data = await self._execute_query(
            USER_QUERY,
            {"username": username, "repoCount": 100},
        )

        response = GithubUserResponse(**data)

        if not response.user:
            raise GithubNotFoundError(f"User {username} not found")

        # Handle pagination if needed
        if response.user.repositories.page_info.get("hasNextPage"):
            logger.info(f"User {username} has >100 repos, fetching remaining pages")
            await self._fetch_remaining_repos(response.user, username)

        return response

    async def _fetch_remaining_repos(self, user, username: str) -> None:
        """Fetch remaining repositories if user has more than 100."""
        cursor = user.repositories.page_info.get("endCursor")
        has_next_page = True

        while has_next_page:
            data = await self._execute_query(
                PAGINATED_REPOS_QUERY,
                {"username": username, "cursor": cursor, "repoCount": 100},
            )

            repos_data = data.get("user", {}).get("repositories", {})
            nodes = repos_data.get("nodes", [])
            page_info = repos_data.get("pageInfo", {})

            # Append to existing repos
            for node in nodes:
                user.repositories.nodes.append(GithubRepository(**node))

            has_next_page = page_info.get("hasNextPage", False)
            cursor = page_info.get("endCursor")

            logger.info(f"Fetched {len(nodes)} more repos for {username}")

    async def fetch_repository_languages(self, owner: str, name: str) -> RepositoryLanguages:
        """Fetch language byte counts for a specific repository."""
        data = await self._execute_query(
            REPO_LANGUAGES_QUERY,
            {"owner": owner, "name": name},
        )

        repo_data = data.get("repository")
        if not repo_data:
            raise GithubNotFoundError(f"Repository {owner}/{name} not found")

        return RepositoryLanguages(**repo_data.get("languages", {"edges": []}))
