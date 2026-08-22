from collections.abc import Generator
from contextlib import contextmanager
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

import psycopg

from app.config import settings


def _build_connection_string(base_url: str) -> str:
    """Build connection string with Supabase-optimized parameters."""
    parsed = urlparse(base_url)
    query_params = parse_qs(parsed.query)
    
    query_params.setdefault("sslmode", ["require"])
    query_params.setdefault("target_session_attrs", ["read-write"])
    
    new_query = urlencode({k: v[0] for k, v in query_params.items()})
    return urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        new_query,
        parsed.fragment,
    ))


@contextmanager
def get_db() -> Generator[psycopg.Connection, None, None]:
    """Get a database connection for each request.
    
    Direct connections work better on Vercel's serverless environment than pooling.
    Each request gets its own fresh connection that's properly closed after use.
    Adds Supabase-recommended SSL and session parameters.
    """
    conn_str = _build_connection_string(settings.database_url)
    conn = psycopg.connect(conn_str, connect_timeout=10)
    try:
        yield conn
    finally:
        conn.close()


def close_pool() -> None:
    """No-op for compatibility with existing code."""
    pass
