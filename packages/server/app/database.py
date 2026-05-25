"""Database engine, session factory, and the declarative base.

SQLite is the default. WAL mode plus a ``busy_timeout`` let a modest number of
workers share one file without tripping over SQLite's single-writer lock (WAL is
also required by Litestream). Swap in Postgres by setting ``DATABASE_URL``.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

settings = get_settings()

_is_sqlite = settings.database_url.startswith("sqlite")

engine = create_engine(
    settings.database_url,
    # SQLite + a threadpool (FastAPI runs sync handlers in threads) needs this.
    connect_args={"check_same_thread": False} if _is_sqlite else {},
    future=True,
)


@event.listens_for(engine, "connect")
def _set_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    """Apply WAL, a busy timeout, and FK enforcement on every SQLite connection."""
    if not _is_sqlite:
        return
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# expire_on_commit=False keeps ORM attributes readable after commit, so handlers
# can build responses from objects without an extra round-trip.
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False, future=True)


class Base(DeclarativeBase):
    """Declarative base for all models."""


def get_db() -> Iterator[Session]:
    """FastAPI dependency yielding a request-scoped session (read paths)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
