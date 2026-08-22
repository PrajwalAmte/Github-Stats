"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-08-22

"""
from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # users table
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username VARCHAR(255) PRIMARY KEY,
            name VARCHAR(255),
            avatar_url TEXT,
            followers INTEGER DEFAULT 0,
            following INTEGER DEFAULT 0,
            public_repos INTEGER DEFAULT 0,
            public_gists INTEGER DEFAULT 0,
            total_commits INTEGER DEFAULT 0,
            total_pull_requests INTEGER DEFAULT 0,
            total_issues INTEGER DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            contribution_count INTEGER DEFAULT 0,
            repository_count INTEGER DEFAULT 0,
            fork_count INTEGER DEFAULT 0,
            star_count INTEGER DEFAULT 0,
            stats_computed_at TIMESTAMP,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_updated_at ON users(updated_at)")

    # repositories table
    op.execute("""
        CREATE TABLE IF NOT EXISTS repositories (
            github_id BIGINT PRIMARY KEY,
            owner VARCHAR(255) NOT NULL,
            name VARCHAR(255) NOT NULL,
            stars INTEGER DEFAULT 0,
            forks INTEGER DEFAULT 0,
            primary_language VARCHAR(100),
            is_fork BOOLEAN DEFAULT FALSE,
            pushed_at TIMESTAMP,
            synced_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_repositories_owner ON repositories(owner)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_repositories_pushed_at ON repositories(pushed_at)")

    # contribution_days table
    op.execute("""
        CREATE TABLE IF NOT EXISTS contribution_days (
            username VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (username, date)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_contribution_days_username_date ON contribution_days(username, date)")

    # language_totals table
    op.execute("""
        CREATE TABLE IF NOT EXISTS language_totals (
            username VARCHAR(255) NOT NULL,
            language VARCHAR(100) NOT NULL,
            byte_count BIGINT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (username, language)
        )
    """)

    # daily_snapshots table
    op.execute("""
        CREATE TABLE IF NOT EXISTS daily_snapshots (
            username VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            total_commits INTEGER DEFAULT 0,
            total_pull_requests INTEGER DEFAULT 0,
            total_issues INTEGER DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            total_stars INTEGER DEFAULT 0,
            total_followers INTEGER DEFAULT 0,
            contribution_count INTEGER DEFAULT 0,
            PRIMARY KEY (username, date)
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_daily_snapshots_username_date ON daily_snapshots(username, date)")

    # sync_state table
    op.execute("""
        CREATE TABLE IF NOT EXISTS sync_state (
            username VARCHAR(255) PRIMARY KEY,
            locked_until TIMESTAMP,
            lock_token VARCHAR(255),
            last_success_at TIMESTAMP,
            last_failure_at TIMESTAMP,
            consecutive_failures INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'ok',
            last_error TEXT,
            updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    op.execute("CREATE INDEX IF NOT EXISTS idx_sync_state_locked_until ON sync_state(locked_until)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS sync_state")
    op.execute("DROP TABLE IF EXISTS daily_snapshots")
    op.execute("DROP TABLE IF EXISTS language_totals")
    op.execute("DROP TABLE IF EXISTS contribution_days")
    op.execute("DROP TABLE IF EXISTS repositories")
    op.execute("DROP TABLE IF EXISTS users")
