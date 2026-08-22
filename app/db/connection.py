from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Get or create SQLAlchemy engine for database connections.
    
    SQLAlchemy handles connection pooling and parameters better than raw psycopg,
    especially in serverless environments like Vercel.
    """
    global _engine
    if _engine is None:
        url = settings.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        
        _engine = create_engine(
            url,
            echo=False,
            pool_size=1,
            max_overflow=0,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={
                "connect_timeout": 10,
                "prepare_threshold": None,  # Disable prepared statements for Supavisor transaction pooling
            },
        )
    return _engine


def get_session() -> sessionmaker[Session]:
    """Get or create session factory."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


@contextmanager
def get_db() -> Generator:
    """Context manager for database operations using SQLAlchemy.
    
    Returns a SQLAlchemy Session that can be used for ORM operations.
    For raw SQL, use session.execute(text("SELECT ..."))
    """
    SessionLocal = get_session()
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def close_pool() -> None:
    """Close the connection pool and reset engine."""
    global _engine, _SessionLocal
    if _engine is not None:
        _engine.dispose()
        _engine = None
        _SessionLocal = None
