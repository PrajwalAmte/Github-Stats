from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.models import (
    ContributionDay,
    DailySnapshot,
    LanguageTotal,
    Repository,
    SyncState,
    User,
)


class UserRepository:
    """Database operations for users."""

    @staticmethod
    def upsert(session: Session, user: User) -> None:
        """Insert or update user profile and statistics."""
        session.execute(
            text(
                """
                INSERT INTO users (
                    username, name, avatar_url, followers, following,
                    public_repos, public_gists, total_commits, total_pull_requests,
                    total_issues, total_reviews, current_streak, longest_streak,
                    contribution_count, repository_count, fork_count, star_count,
                    stats_computed_at, updated_at
                ) VALUES (
                    :username, :name, :avatar_url, :followers, :following,
                    :public_repos, :public_gists, :total_commits, :total_pull_requests,
                    :total_issues, :total_reviews, :current_streak, :longest_streak,
                    :contribution_count, :repository_count, :fork_count, :star_count,
                    :stats_computed_at, :updated_at
                )
                ON CONFLICT (username) DO UPDATE SET
                    name = EXCLUDED.name,
                    avatar_url = EXCLUDED.avatar_url,
                    followers = EXCLUDED.followers,
                    following = EXCLUDED.following,
                    public_repos = EXCLUDED.public_repos,
                    public_gists = EXCLUDED.public_gists,
                    total_commits = EXCLUDED.total_commits,
                    total_pull_requests = EXCLUDED.total_pull_requests,
                    total_issues = EXCLUDED.total_issues,
                    total_reviews = EXCLUDED.total_reviews,
                    current_streak = EXCLUDED.current_streak,
                    longest_streak = EXCLUDED.longest_streak,
                    contribution_count = EXCLUDED.contribution_count,
                    repository_count = EXCLUDED.repository_count,
                    fork_count = EXCLUDED.fork_count,
                    star_count = EXCLUDED.star_count,
                    stats_computed_at = EXCLUDED.stats_computed_at,
                    updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "username": user.username,
                "name": user.name,
                "avatar_url": user.avatar_url,
                "followers": user.followers,
                "following": user.following,
                "public_repos": user.public_repos,
                "public_gists": user.public_gists,
                "total_commits": user.total_commits,
                "total_pull_requests": user.total_pull_requests,
                "total_issues": user.total_issues,
                "total_reviews": user.total_reviews,
                "current_streak": user.current_streak,
                "longest_streak": user.longest_streak,
                "contribution_count": user.contribution_count,
                "repository_count": user.repository_count,
                "fork_count": user.fork_count,
                "star_count": user.star_count,
                "stats_computed_at": user.stats_computed_at,
                "updated_at": user.updated_at,
            },
        )

    @staticmethod
    def get_by_username(session: Session, username: str) -> User | None:
        """Retrieve user by username."""
        result = session.execute(
            text("SELECT * FROM users WHERE username = :username"),
            {"username": username},
        )
        row = result.mappings().first()
        return User(**dict(row)) if row else None


class RepositoryRepository:
    """Database operations for repositories."""

    @staticmethod
    def upsert_many(session: Session, repos: list[Repository]) -> None:
        """Bulk upsert repositories."""
        if not repos:
            return

        for r in repos:
            session.execute(
                text(
                    """
                    INSERT INTO repositories (
                        github_id, owner, name, stars, forks, primary_language,
                        is_fork, pushed_at, synced_at
                    ) VALUES (
                        :github_id, :owner, :name, :stars, :forks, :primary_language,
                        :is_fork, :pushed_at, :synced_at
                    )
                    ON CONFLICT (github_id) DO UPDATE SET
                        owner = EXCLUDED.owner,
                        name = EXCLUDED.name,
                        stars = EXCLUDED.stars,
                        forks = EXCLUDED.forks,
                        primary_language = EXCLUDED.primary_language,
                        is_fork = EXCLUDED.is_fork,
                        pushed_at = EXCLUDED.pushed_at,
                        synced_at = EXCLUDED.synced_at
                    """
                ),
                {
                    "github_id": r.github_id,
                    "owner": r.owner,
                    "name": r.name,
                    "stars": r.stars,
                    "forks": r.forks,
                    "primary_language": r.primary_language,
                    "is_fork": r.is_fork,
                    "pushed_at": r.pushed_at,
                    "synced_at": r.synced_at,
                },
            )


class ContributionRepository:
    """Database operations for contribution days."""

    @staticmethod
    def upsert_many(session: Session, contributions: list[ContributionDay]) -> None:
        """Bulk upsert contribution days."""
        if not contributions:
            return

        for c in contributions:
            session.execute(
                text(
                    """
                    INSERT INTO contribution_days (username, date, count)
                    VALUES (:username, :date, :count)
                    ON CONFLICT (username, date) DO UPDATE SET
                        count = EXCLUDED.count
                    """
                ),
                {
                    "username": c.username,
                    "date": c.date,
                    "count": c.count,
                },
            )

    @staticmethod
    def get_all_for_user(session: Session, username: str) -> list[ContributionDay]:
        """Get all contribution days for a user."""
        result = session.execute(
            text("SELECT * FROM contribution_days WHERE username = :username ORDER BY date"),
            {"username": username},
        )
        return [ContributionDay(**dict(row)) for row in result.mappings()]


class LanguageRepository:
    """Database operations for language totals."""

    @staticmethod
    def upsert_many(session: Session, languages: list[LanguageTotal]) -> None:
        """Bulk upsert language totals."""
        if not languages:
            return

        for lang in languages:
            session.execute(
                text(
                    """
                    INSERT INTO language_totals (username, language, byte_count, updated_at)
                    VALUES (:username, :language, :byte_count, :updated_at)
                    ON CONFLICT (username, language) DO UPDATE SET
                        byte_count = EXCLUDED.byte_count,
                        updated_at = EXCLUDED.updated_at
                    """
                ),
                {
                    "username": lang.username,
                    "language": lang.language,
                    "byte_count": lang.byte_count,
                    "updated_at": lang.updated_at,
                },
            )

    @staticmethod
    def get_all_for_user(session: Session, username: str) -> list[LanguageTotal]:
        """Get all language totals for a user."""
        result = session.execute(
            text(
                """
                SELECT * FROM language_totals
                WHERE username = :username
                ORDER BY byte_count DESC
                """
            ),
            {"username": username},
        )
        return [LanguageTotal(**dict(row)) for row in result.mappings()]


class SnapshotRepository:
    """Database operations for daily snapshots."""

    @staticmethod
    def upsert(session: Session, snapshot: DailySnapshot) -> None:
        """Insert or update daily snapshot."""
        session.execute(
            text(
                """
                INSERT INTO daily_snapshots (
                    username, date, total_commits, total_pull_requests,
                    total_issues, total_reviews, total_stars, total_followers,
                    contribution_count
                ) VALUES (
                    :username, :date, :total_commits, :total_pull_requests,
                    :total_issues, :total_reviews, :total_stars, :total_followers,
                    :contribution_count
                )
                ON CONFLICT (username, date) DO UPDATE SET
                    total_commits = EXCLUDED.total_commits,
                    total_pull_requests = EXCLUDED.total_pull_requests,
                    total_issues = EXCLUDED.total_issues,
                    total_reviews = EXCLUDED.total_reviews,
                    total_stars = EXCLUDED.total_stars,
                    total_followers = EXCLUDED.total_followers,
                    contribution_count = EXCLUDED.contribution_count
                """
            ),
            {
                "username": snapshot.username,
                "date": snapshot.date,
                "total_commits": snapshot.total_commits,
                "total_pull_requests": snapshot.total_pull_requests,
                "total_issues": snapshot.total_issues,
                "total_reviews": snapshot.total_reviews,
                "total_stars": snapshot.total_stars,
                "total_followers": snapshot.total_followers,
                "contribution_count": snapshot.contribution_count,
            },
        )

    @staticmethod
    def get_range(
        session: Session, username: str, start_date: date, end_date: date
    ) -> list[DailySnapshot]:
        """Get daily snapshots for a date range."""
        result = session.execute(
            text(
                """
                SELECT * FROM daily_snapshots
                WHERE username = :username AND date >= :start_date AND date <= :end_date
                ORDER BY date
                """
            ),
            {
                "username": username,
                "start_date": start_date,
                "end_date": end_date,
            },
        )
        return [DailySnapshot(**dict(row)) for row in result.mappings()]


class SyncStateRepository:
    """Database operations for sync state."""

    @staticmethod
    def get(session: Session, username: str) -> SyncState | None:
        """Get sync state for a user."""
        result = session.execute(
            text("SELECT * FROM sync_state WHERE username = :username"),
            {"username": username},
        )
        row = result.mappings().first()
        return SyncState(**dict(row)) if row else None

    @staticmethod
    def update_success(session: Session, username: str) -> None:
        """Mark sync as successful."""
        session.execute(
            text(
                """
                INSERT INTO sync_state (
                    username, last_success_at, consecutive_failures,
                    status, last_error, updated_at
                ) VALUES (:username, NOW(), 0, 'ok', NULL, NOW())
                ON CONFLICT (username) DO UPDATE SET
                    last_success_at = NOW(),
                    consecutive_failures = 0,
                    status = 'ok',
                    last_error = NULL,
                    locked_until = NULL,
                    lock_token = NULL,
                    updated_at = NOW()
                """
            ),
            {"username": username},
        )
        session.commit()

    @staticmethod
    def update_failure(session: Session, username: str, error: str) -> None:
        """Record sync failure."""
        session.execute(
            text(
                """
                INSERT INTO sync_state (
                    username, last_failure_at, consecutive_failures,
                    status, last_error, updated_at
                ) VALUES (:username, NOW(), 1, 'degraded', :error, NOW())
                ON CONFLICT (username) DO UPDATE SET
                    last_failure_at = NOW(),
                    consecutive_failures = sync_state.consecutive_failures + 1,
                    status = CASE
                        WHEN sync_state.consecutive_failures + 1 >= 3 THEN 'degraded'
                        WHEN sync_state.consecutive_failures + 1 >= 5 THEN 'failing'
                        ELSE sync_state.status
                    END,
                    last_error = :error,
                    locked_until = NULL,
                    lock_token = NULL,
                    updated_at = NOW()
                """
            ),
            {"username": username, "error": error},
        )
        session.commit()

    @staticmethod
    def acquire_lock(session: Session, username: str, token: str, duration_seconds: int) -> bool:
        """
        Attempt to acquire sync lock.
        Returns True if lock was acquired, False if already locked.
        """
        result = session.execute(
            text(
                """
                INSERT INTO sync_state (username, locked_until, lock_token, updated_at)
                VALUES (:username, NOW() + make_interval(secs => :duration), :token, NOW())
                ON CONFLICT (username) DO UPDATE SET
                    locked_until = NOW() + make_interval(secs => :duration),
                    lock_token = :token,
                    updated_at = NOW()
                WHERE sync_state.username = :username
                  AND (sync_state.locked_until IS NULL OR sync_state.locked_until < NOW())
                """
            ),
            {
                "username": username,
                "duration": duration_seconds,
                "token": token,
            },
        )
        return result.rowcount > 0

    @staticmethod
    def release_lock(session: Session, username: str, token: str) -> None:
        """Release sync lock if token matches."""
        session.execute(
            text(
                """
                UPDATE sync_state
                SET locked_until = NULL, lock_token = NULL, updated_at = NOW()
                WHERE username = :username AND lock_token = :token
                """
            ),
            {"username": username, "token": token},
        )
        session.commit()
