from collections.abc import Generator
from contextlib import contextmanager

import psycopg

from app.config import settings


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    """Get a database connection for each request.
    
    Direct connections work better on Vercel's serverless environment than pooling.
    Each request gets its own fresh connection that's properly closed after use.
    """
    url = settings.database_url
    if "?sslmode" not in url:
        url += "?sslmode=require" if "?" not in url else "&sslmode=require"
    
    conn = psycopg.connect(url, connect_timeout=10)
    try:
        yield conn
    finally:
        conn.close()


def close_pool() -> None:
    """No-op for compatibility with existing code."""
    pass
