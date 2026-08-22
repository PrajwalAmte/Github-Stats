from collections.abc import Generator
from contextlib import contextmanager

import psycopg

from app.config import settings


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    """Get a database connection.
    
    Uses direct connections instead of pooling for better serverless compatibility.
    Each request gets its own connection, which is properly closed after use.
    Uses Supabase-recommended connection parameters.
    """
    conn = psycopg.connect(settings.database_url_with_params, connect_timeout=10)
    try:
        yield conn
    finally:
        conn.close()


def close_pool() -> None:
    """No-op for compatibility with existing code."""
    pass
