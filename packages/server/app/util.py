"""Small shared helpers (kept tiny on purpose)."""

from datetime import datetime, timezone


def utcnow() -> datetime:
    """Naive UTC ``datetime``.

    We store and compare naive UTC everywhere so SQLite (which has no native
    timezone storage) never mixes aware and naive values.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)


def iso(dt: datetime | None) -> str | None:
    """Format a stored naive-UTC datetime as ISO-8601 with a ``Z`` suffix."""
    if dt is None:
        return None
    return dt.replace(microsecond=0).isoformat() + "Z"
