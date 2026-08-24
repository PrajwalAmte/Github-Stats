"""Synchronization service - orchestrates GitHub data sync with database."""

import asyncio
import logging
import secrets
from datetime import date, datetime

from app.config import settings
from app.db.connection import get_db
from app.db.models import ContributionDay, LanguageTotal, Repository, User
from app.db.repositories import (
    ContributionRepository,
    LanguageRepository,
    RepositoryRepository,
    SnapshotRepository,
    SyncStateRepository,
    UserRepository,
)
from app.exceptions import GithubApiError, SyncAlreadyRunningError
from app.github.client import GithubClient
from app.stats.metrics import compute_user_aggregates, create_daily_snapshot
from app.stats.streaks import calculate_contribution_total, calculate_streaks

logger = logging.getLogger(__name__)

# Cap on concurrent GitHub requests for per-repo language data. Bounded
# rather than unlimited to stay well under GitHub's secondary rate
# limits when an account has many repos.
LANGUAGE_FETCH_CONCURRENCY = 5

# Overall wall-clock cap on the language-fetch phase. Set comfortably
# under the caller's request timeout (the GitHub Actions curl uses
# --max-time 45) so a slow/large account times out on its own terms
# with partial data, instead of the whole HTTP request hanging until
# the caller gives up first.
LANGUAGE_FETCH_BUDGET_SECONDS = 25


# Synchronous DB operations
# These use the blocking SQLAlchemy session directly and are ONLY ever
# called via asyncio.to_thread from async code below. Calling any of
# these directly inside `async def` freezes the event loop for the
# duration of the DB round-trip — that was the root cause of requests
# (including unrelated ones on the same instance) hanging.


def _acquire_lock_sync(username: str, lock_token: str) -> bool:
    with get_db() as session:
        acquired = SyncStateRepository.acquire_lock(
            session, username, lock_token, settings.sync_lock_duration_seconds
        )
        session.commit()
    return acquired


def _persist_sync_sync(
    username: str,
    repositories: list[Repository],
    contributions: list[tuple[date, int]],
    languages: list[LanguageTotal],
    user_row: User,
    snapshot,
) -> None:
    with get_db() as session:
        try:
            RepositoryRepository.upsert_many(session, repositories)

            contribution_models = [
                ContributionDay(username=username, date=d, count=c) for d, c in contributions
            ]
            ContributionRepository.upsert_many(session, contribution_models)

            LanguageRepository.upsert_many(session, languages)
            UserRepository.upsert(session, user_row)
            SnapshotRepository.upsert(session, snapshot)
            SyncStateRepository.update_success(session, username)

            session.commit()
        except Exception:
            session.rollback()
            raise


def _record_failure_sync(username: str, error_msg: str) -> None:
    with get_db() as session:
        SyncStateRepository.update_failure(session, username, error_msg)
        session.commit()


def _release_lock_sync(username: str, lock_token: str) -> None:
    with get_db() as session:
        SyncStateRepository.release_lock(session, username, lock_token)
        session.commit()


def trigger_background_sync(username: str) -> None:
    """Retired — replaced by `sync_user_background` below, wired through
    FastAPI's BackgroundTasks instead of a detached Thread.

    The Thread + new-event-loop version was unreliable specifically
    because this runs on serverless: a function invocation is treated
    as complete once the HTTP response is sent, and the platform can
    freeze or kill the process at that point. A detached thread isn't
    awaited by anything in the request lifecycle, so it could be
    starved before doing any real work. BackgroundTasks IS part of the
    ASGI lifecycle — Starlette runs it before the invocation is
    signaled complete — which is what actually guarantees it runs.
    """
    raise NotImplementedError("Use sync_user_background via FastAPI BackgroundTasks instead")


async def sync_user_background(username: str) -> None:
    """Fire-and-forget sync for BackgroundTasks: reuses the singleton
    sync_service (no second GithubClient, no second event loop) and
    swallows errors since there's no request left to report them to —
    they're already logged and recorded in sync_state by sync_user
    itself.
    """
    try:
        await sync_service.sync_user(username)
    except SyncAlreadyRunningError:
        pass  # another request is already syncing this user — fine
    except Exception as e:
        logger.warning(f"Background first-sync for {username} failed: {e}")


class SyncService:
    """Synchronization service for GitHub data."""

    def __init__(self):
        self.github_client = GithubClient()

    async def sync_user(self, username: str) -> dict:
        """
        Synchronize GitHub data for a user.

        This is the main entry point for synchronization. It:
        1. Acquires a lock to prevent concurrent syncs
        2. Fetches data from GitHub (outside transaction)
        3. Performs atomic database updates (inside transaction)
        4. Records success/failure state

        All DB work runs via asyncio.to_thread so it never blocks the
        event loop that other requests on this instance depend on.

        Raises:
            SyncAlreadyRunningError: If sync is already in progress
            GithubApiError: If GitHub API fails
        """
        lock_token = secrets.token_hex(16)

        acquired = await asyncio.to_thread(_acquire_lock_sync, username, lock_token)
        if not acquired:
            raise SyncAlreadyRunningError(f"Sync already running for {username}")

        try:
            logger.info(f"Fetching GitHub data for {username}")
            github_data = await self.github_client.fetch_user_data(username)

            if not github_data.user:
                raise GithubApiError(f"No user data returned for {username}")

            user_data = github_data.user

            contributions = self._extract_contributions(user_data)
            repositories = self._extract_repositories(user_data, username)
            languages = await self._fetch_languages(username, repositories)

            current_streak, longest_streak = calculate_streaks(contributions)
            contribution_count = calculate_contribution_total(contributions)

            cc = user_data.contributions_collection
            github_totals = {
                "totalCommitContributions": cc.total_commit_contributions,
                "totalPullRequestContributions": cc.total_pull_request_contributions,
                "totalIssueContributions": cc.total_issue_contributions,
                "totalPullRequestReviewContributions": cc.total_pull_request_review_contributions,
            }

            aggregates = compute_user_aggregates(
                github_totals=github_totals,
                current_streak=current_streak,
                longest_streak=longest_streak,
                contribution_count=contribution_count,
                repo_count=len(repositories),
                total_stars=sum(r.stars for r in repositories),
                total_forks=sum(r.forks for r in repositories),
            )

            user = User(
                username=username,
                name=user_data.name,
                avatar_url=user_data.avatar_url,
                followers=user_data.followers.total_count,
                following=user_data.following.total_count,
                public_repos=len(repositories),
                total_commits=aggregates.total_commits,
                total_pull_requests=aggregates.total_pull_requests,
                total_issues=aggregates.total_issues,
                total_reviews=aggregates.total_reviews,
                current_streak=aggregates.current_streak,
                longest_streak=aggregates.longest_streak,
                contribution_count=aggregates.contribution_count,
                repository_count=aggregates.repository_count,
                star_count=aggregates.star_count,
                fork_count=aggregates.fork_count,
                stats_computed_at=datetime.now(),
                updated_at=datetime.now(),
            )
            snapshot = create_daily_snapshot(username, user, user_data.followers.total_count)

            await asyncio.to_thread(
                _persist_sync_sync,
                username,
                repositories,
                contributions,
                languages,
                user,
                snapshot,
            )

            logger.info(f"Successfully synced {username}")

            return {
                "username": username,
                "status": "success",
                "repositories_synced": len(repositories),
                "contribution_days": len(contributions),
            }

        except GithubApiError as e:
            error_msg = str(e)
            logger.error(f"GitHub API error for {username}: {error_msg}")
            await asyncio.to_thread(_record_failure_sync, username, error_msg)
            raise

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Sync error for {username}: {error_msg}", exc_info=True)
            await asyncio.to_thread(_record_failure_sync, username, error_msg)
            raise

        finally:
            await asyncio.to_thread(_release_lock_sync, username, lock_token)

    def _extract_contributions(self, user_data) -> list[tuple[date, int]]:
        """Extract contribution days from GitHub user data."""
        contributions = []
        weeks = user_data.contributions_collection.contribution_calendar.weeks

        for week in weeks:
            for day in week.contribution_days:
                day_date = datetime.strptime(day.date, "%Y-%m-%d").date()
                contributions.append((day_date, day.contribution_count))

        return contributions

    def _extract_repositories(self, user_data, username: str) -> list[Repository]:
        """Extract repository data from GitHub user data."""
        repositories = []

        for repo in user_data.repositories.nodes:
            primary_lang = repo.primary_language.name if repo.primary_language else None
            pushed_at = (
                datetime.fromisoformat(repo.pushed_at.replace("Z", "+00:00"))
                if repo.pushed_at
                else None
            )

            repositories.append(
                Repository(
                    github_id=repo.database_id,
                    owner=username,
                    name=repo.name,
                    stars=repo.stargazer_count,
                    forks=repo.fork_count,
                    primary_language=primary_lang,
                    is_fork=repo.is_fork,
                    pushed_at=pushed_at,
                    synced_at=datetime.now(),
                )
            )

        return repositories

    async def _fetch_languages(
        self, username: str, repositories: list[Repository]
    ) -> list[LanguageTotal]:
        """Fetch detailed language data for non-fork repositories.

        Runs with bounded concurrency instead of one repo at a time —
        for an account with many repos, sequential awaits was likely
        the main reason single sync requests ran long enough to
        approach the 45s ceiling on their own.

        NOT YET DONE: filtering to only repos whose `pushed_at` is
        newer than the last successful sync, which was the original
        design to avoid re-fetching unchanged repos every run. That
        needs a read path into SyncStateRepository (or the user's
        prior stats_computed_at) that I don't have visibility into —
        share that module and this can be tightened further. That
        filter is what actually bounds the *number* of calls; the
        deadline below only bounds the *time*, so an account with
        many repos still degrades to partial language data rather
        than fixing the root cause.
        """
        targets = [repo for repo in repositories if not repo.is_fork]
        language_totals: dict[str, int] = {}
        semaphore = asyncio.Semaphore(LANGUAGE_FETCH_CONCURRENCY)

        async def fetch_one(repo: Repository) -> None:
            async with semaphore:
                try:
                    lang_data = await self.github_client.fetch_repository_languages(
                        repo.owner, repo.name
                    )
                except Exception as e:
                    logger.warning(f"Failed to fetch languages for {repo.owner}/{repo.name}: {e}")
                    return

                if lang_data and lang_data.edges:
                    for lang_edge in lang_data.edges:
                        lang_name = lang_edge.node.get("name")
                        if lang_name:
                            language_totals[lang_name] = (
                                language_totals.get(lang_name, 0) + lang_edge.size
                            )

        try:
            # Overall budget for the whole phase, not per-call. Each
            # individual call is already capped (see github/client.py),
            # but with enough repos the batches still add up past the
            # sync's real time budget — this caps the total instead.
            # On timeout, whatever's already landed in language_totals
            # stays; we return partial data rather than blocking the
            # entire sync (and the HTTP response) indefinitely.
            await asyncio.wait_for(
                asyncio.gather(*(fetch_one(repo) for repo in targets)),
                timeout=LANGUAGE_FETCH_BUDGET_SECONDS,
            )
        except TimeoutError:
            logger.warning(
                f"Language fetch for {username} exceeded "
                f"{LANGUAGE_FETCH_BUDGET_SECONDS}s budget with {len(targets)} repos — "
                f"returning partial results ({len(language_totals)} languages collected)"
            )

        now = datetime.now()
        return [
            LanguageTotal(
                username=username,
                language=lang_name,
                byte_count=byte_count,
                updated_at=now,
            )
            for lang_name, byte_count in language_totals.items()
        ]


# Singleton instance
sync_service = SyncService()
