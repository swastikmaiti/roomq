"""Transactional write helper.

Mutating endpoints run their work through :func:`run_write`, which opens a
fresh session, commits on success, rolls back on any error, and retries the
whole transaction on a transient ``OperationalError`` (per ``io_retry``).

Read-only endpoints use the request-scoped ``get_db`` session directly — WAL
readers don't block, so they need no retry.
"""

from collections.abc import Callable
from typing import TypeVar

from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.services.retry import io_retry

T = TypeVar("T")


def run_write(work: Callable[[Session], T]) -> T:
    """Run ``work(session)`` in a retried, all-or-nothing transaction.

    ``work`` should perform its reads and writes on the given session and return
    whatever the caller needs for the response. The session is committed before
    this returns; with ``expire_on_commit=False`` the returned ORM objects stay
    usable.
    """

    @io_retry
    def _attempt() -> T:
        session = SessionLocal()
        try:
            result = work(session)
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    return _attempt()
