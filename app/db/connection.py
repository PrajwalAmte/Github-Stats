from collections.abc import Generator
from contextlib import contextmanager

import psycopg
from psycopg_pool import ConnectionPool

from app.config import settings

# Connection pool for serverless-friendly connection management
_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get or create the connection pool."""
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            conninfo=settings.database_url,
            min_size=0,
            max_size=5,
            timeout=10,
            connect_kwargs={"connect_timeout": 10},
        )
    return _pool


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    """Get a database connection from the pool."""
    pool = get_pool()
    with pool.connection() as conn:
        yield conn


def close_pool() -> None:
    """Close the connection pool."""
    global _pool
    if _pool is not None:
        _pool.close()
        _pool = None
