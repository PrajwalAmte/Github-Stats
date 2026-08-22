from datetime import date

import psycopg
from psycopg.rows import dict_row

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
    def upsert(conn: psycopg.Connection, user: User) -> None:
        """Insert or update user profile and statistics."""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO users (
                    username, name, avatar_url, followers, following,
                    public_repos, public_gists, total_commits, total_pull_requests,
                    total_issues, total_reviews, current_streak, longest_streak,
                    contribution_count, repository_count, fork_count, star_count,
                    stats_computed_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
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
                """,
                (
                    user.username,
                    user.name,
                    user.avatar_url,
                    user.followers,
                    user.following,
                    user.public_repos,
                    user.public_gists,
                    user.total_commits,
                    user.total_pull_requests,
                    user.total_issues,
                    user.total_reviews,
                    user.current_streak,
                    user.longest_streak,
                    user.contribution_count,
                    user.repository_count,
                    user.fork_count,
                    user.star_count,
                    user.stats_computed_at,
                    user.updated_at,
                ),
            )

    @staticmethod
    def get_by_username(conn: psycopg.Connection, username: str) -> User | None:
        """Retrieve user by username."""
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            return User(**row) if row else None


class RepositoryRepository:
    """Database operations for repositories."""

    @staticmethod
    def upsert_many(conn: psycopg.Connection, repos: list[Repository]) -> None:
        """Bulk upsert repositories."""
        if not repos:
            return

        with conn.cursor() as cur:
            data = [
                (
                    r.github_id,
                    r.owner,
                    r.name,
                    r.stars,
                    r.forks,
                    r.primary_language,
                    r.is_fork,
                    r.pushed_at,
                    r.synced_at,
                )
                for r in repos
            ]
            cur.executemany(
                """
                INSERT INTO repositories (
                    github_id, owner, name, stars, forks, primary_language,
                    is_fork, pushed_at, synced_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (github_id) DO UPDATE SET
                    owner = EXCLUDED.owner,
                    name = EXCLUDED.name,
                    stars = EXCLUDED.stars,
                    forks = EXCLUDED.forks,
                    primary_language = EXCLUDED.primary_language,
                    is_fork = EXCLUDED.is_fork,
                    pushed_at = EXCLUDED.pushed_at,
                    synced_at = EXCLUDED.synced_at
                """,
                data,
            )


class ContributionRepository:
    """Database operations for contribution days."""

    @staticmethod
    def upsert_many(conn: psycopg.Connection, contributions: list[ContributionDay]) -> None:
        """Bulk upsert contribution days."""
        if not contributions:
            return

        with conn.cursor() as cur:
            data = [(c.username, c.date, c.count) for c in contributions]
            cur.executemany(
                """
                INSERT INTO contribution_days (username, date, count)
                VALUES (%s, %s, %s)
                ON CONFLICT (username, date) DO UPDATE SET
                    count = EXCLUDED.count
                """,
                data,
            )

    @staticmethod
    def get_all_for_user(conn: psycopg.Connection, username: str) -> list[ContributionDay]:
        """Get all contribution days for a user."""
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM contribution_days WHERE username = %s ORDER BY date",
                (username,),
            )
            return [ContributionDay(**row) for row in cur.fetchall()]


class LanguageRepository:
    """Database operations for language totals."""

    @staticmethod
    def upsert_many(conn: psycopg.Connection, languages: list[LanguageTotal]) -> None:
        """Bulk upsert language totals."""
        if not languages:
            return

        with conn.cursor() as cur:
            data = [
                (lang.username, lang.language, lang.byte_count, lang.updated_at) for lang in languages
            ]
            cur.executemany(
                """
                INSERT INTO language_totals (username, language, byte_count, updated_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (username, language) DO UPDATE SET
                    byte_count = EXCLUDED.byte_count,
                    updated_at = EXCLUDED.updated_at
                """,
                data,
            )

    @staticmethod
    def get_all_for_user(conn: psycopg.Connection, username: str) -> list[LanguageTotal]:
        """Get all language totals for a user."""
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                "SELECT * FROM language_totals WHERE username = %s ORDER BY byte_count DESC",
                (username,),
            )
            return [LanguageTotal(**row) for row in cur.fetchall()]


class SnapshotRepository:
    """Database operations for daily snapshots."""

    @staticmethod
    def upsert(conn: psycopg.Connection, snapshot: DailySnapshot) -> None:
        """Insert or update daily snapshot."""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO daily_snapshots (
                    username, date, total_commits, total_pull_requests,
                    total_issues, total_reviews, total_stars, total_followers,
                    contribution_count
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (username, date) DO UPDATE SET
                    total_commits = EXCLUDED.total_commits,
                    total_pull_requests = EXCLUDED.total_pull_requests,
                    total_issues = EXCLUDED.total_issues,
                    total_reviews = EXCLUDED.total_reviews,
                    total_stars = EXCLUDED.total_stars,
                    total_followers = EXCLUDED.total_followers,
                    contribution_count = EXCLUDED.contribution_count
                """,
                (
                    snapshot.username,
                    snapshot.date,
                    snapshot.total_commits,
                    snapshot.total_pull_requests,
                    snapshot.total_issues,
                    snapshot.total_reviews,
                    snapshot.total_stars,
                    snapshot.total_followers,
                    snapshot.contribution_count,
                ),
            )

    @staticmethod
    def get_range(
        conn: psycopg.Connection, username: str, start_date: date, end_date: date
    ) -> list[DailySnapshot]:
        """Get daily snapshots for a date range."""
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(
                """
                SELECT * FROM daily_snapshots
                WHERE username = %s AND date >= %s AND date <= %s
                ORDER BY date
                """,
                (username, start_date, end_date),
            )
            return [DailySnapshot(**row) for row in cur.fetchall()]


class SyncStateRepository:
    """Database operations for sync state."""

    @staticmethod
    def get(conn: psycopg.Connection, username: str) -> SyncState | None:
        """Get sync state for a user."""
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT * FROM sync_state WHERE username = %s", (username,))
            row = cur.fetchone()
            return SyncState(**row) if row else None

    @staticmethod
    def update_success(conn: psycopg.Connection, username: str) -> None:
        """Mark sync as successful."""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sync_state (
                    username, last_success_at, consecutive_failures,
                    status, last_error, updated_at
                ) VALUES (%s, NOW(), 0, 'ok', NULL, NOW())
                ON CONFLICT (username) DO UPDATE SET
                    last_success_at = NOW(),
                    consecutive_failures = 0,
                    status = 'ok',
                    last_error = NULL,
                    locked_until = NULL,
                    lock_token = NULL,
                    updated_at = NOW()
                """,
                (username,),
            )

    @staticmethod
    def update_failure(conn: psycopg.Connection, username: str, error: str) -> None:
        """Record sync failure."""
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sync_state (
                    username, last_failure_at, consecutive_failures,
                    status, last_error, updated_at
                ) VALUES (%s, NOW(), 1, 'degraded', %s, NOW())
                ON CONFLICT (username) DO UPDATE SET
                    last_failure_at = NOW(),
                    consecutive_failures = sync_state.consecutive_failures + 1,
                    status = CASE
                        WHEN sync_state.consecutive_failures + 1 >= 3 THEN 'degraded'
                        WHEN sync_state.consecutive_failures + 1 >= 5 THEN 'failing'
                        ELSE sync_state.status
                    END,
                    last_error = %s,
                    locked_until = NULL,
                    lock_token = NULL,
                    updated_at = NOW()
                """,
                (username, error, error),
            )

    @staticmethod
    def acquire_lock(
        conn: psycopg.Connection, username: str, token: str, duration_seconds: int
    ) -> bool:
        """
        Attempt to acquire sync lock.
        Returns True if lock was acquired, False if already locked.
        """
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO sync_state (username, locked_until, lock_token, updated_at)
                VALUES (%s, NOW() + make_interval(secs => %s), %s, NOW())
                ON CONFLICT (username) DO UPDATE SET
                    locked_until = NOW() + make_interval(secs => %s),
                    lock_token = %s,
                    updated_at = NOW()
                WHERE sync_state.username = %s
                  AND (sync_state.locked_until IS NULL OR sync_state.locked_until < NOW())
                """,
                (username, duration_seconds, token, duration_seconds, token, username),
            )
            return cur.rowcount > 0

    @staticmethod
    def release_lock(conn: psycopg.Connection, username: str, token: str) -> None:
        """Release sync lock if token matches."""
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE sync_state
                SET locked_until = NULL, lock_token = NULL, updated_at = NOW()
                WHERE username = %s AND lock_token = %s
                """,
                (username, token),
            )
