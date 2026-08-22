"""Synchronization service - orchestrates GitHub data sync with database."""

import logging
import secrets
from datetime import date, datetime

from app.config import settings
from app.db.connection import get_db
from app.db.models import ContributionDay, Repository, User
from app.db.repositories import (
    ContributionRepository,
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

        Args:
            username: GitHub username to sync

        Returns:
            Dict with sync result information

        Raises:
            SyncAlreadyRunningError: If sync is already in progress
            GithubApiError: If GitHub API fails
        """
        lock_token = secrets.token_hex(16)

        # Acquire lock
        with get_db() as session:
            acquired = SyncStateRepository.acquire_lock(
                session, username, lock_token, settings.sync_lock_duration_seconds
            )
            session.commit()

        if not acquired:
            raise SyncAlreadyRunningError(f"Sync already running for {username}")

        try:
            # Fetch data from GitHub (outside transaction - no DB lock held)
            logger.info(f"Fetching GitHub data for {username}")
            github_data = await self.github_client.fetch_user_data(username)

            if not github_data.user:
                raise GithubApiError(f"No user data returned for {username}")

            user_data = github_data.user

            # Process and validate data
            contributions = self._extract_contributions(user_data)
            repositories = self._extract_repositories(user_data, username)

            # Calculate aggregates
            current_streak, longest_streak = calculate_streaks(contributions)
            contribution_count = calculate_contribution_total(contributions)

            repo_count = len(repositories)
            total_stars = sum(r.stars for r in repositories)
            total_forks = sum(r.forks for r in repositories)

            github_totals = {
                "totalCommitContributions": user_data.contributions_collection.total_commit_contributions,
                "totalPullRequestContributions": user_data.contributions_collection.total_pull_request_contributions,
                "totalIssueContributions": user_data.contributions_collection.total_issue_contributions,
                "totalPullRequestReviewContributions": user_data.contributions_collection.total_pull_request_review_contributions,
            }

            aggregates = compute_user_aggregates(
                github_totals=github_totals,
                current_streak=current_streak,
                longest_streak=longest_streak,
                contribution_count=contribution_count,
                repo_count=repo_count,
                total_stars=total_stars,
                total_forks=total_forks,
            )

            # Atomic database update - all or nothing
            with get_db() as session:
                try:
                    # Upsert repositories
                    RepositoryRepository.upsert_many(session, repositories)

                    # Upsert contribution days
                    contribution_models = [
                        ContributionDay(username=username, date=d, count=c)
                        for d, c in contributions
                    ]
                    ContributionRepository.upsert_many(session, contribution_models)

                    # Update user with aggregates
                    user = User(
                        username=username,
                        name=user_data.name,
                        avatar_url=user_data.avatar_url,
                        followers=user_data.followers.total_count,
                        following=user_data.following.total_count,
                        public_repos=repo_count,
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
                    UserRepository.upsert(session, user)

                    # Create daily snapshot
                    snapshot = create_daily_snapshot(
                        username, user, user_data.followers.total_count
                    )
                    SnapshotRepository.upsert(session, snapshot)

                    # Mark sync as successful
                    SyncStateRepository.update_success(session, username)

                    session.commit()
                except Exception as e:
                    session.rollback()
                    raise

            logger.info(f"Successfully synced {username}")

            return {
                "username": username,
                "status": "success",
                "repositories_synced": len(repositories),
                "contribution_days": len(contributions),
            }

        except GithubApiError as e:
            # Record failure but don't modify user-facing data
            error_msg = str(e)
            logger.error(f"GitHub API error for {username}: {error_msg}")

            with get_db() as session:
                SyncStateRepository.update_failure(session, username, error_msg)
                session.commit()

            raise

        except Exception as e:
            # Unexpected error - record it
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"Sync error for {username}: {error_msg}", exc_info=True)

            with get_db() as session:
                SyncStateRepository.update_failure(session, username, error_msg)
                session.commit()

            raise

        finally:
            # Always release the lock
            with get_db() as session:
                SyncStateRepository.release_lock(session, username, lock_token)
                session.commit()

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
            primary_lang = None
            if repo.primary_language:
                primary_lang = repo.primary_language.name

            pushed_at = None
            if repo.pushed_at:
                pushed_at = datetime.fromisoformat(repo.pushed_at.replace("Z", "+00:00"))

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


# Singleton instance
sync_service = SyncService()
