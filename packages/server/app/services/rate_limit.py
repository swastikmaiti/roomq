"""Fixed-window rate limiting backed by ``RateLimitBucket`` rows.

Each (scope, bucket) is counted within an aligned time window. Calls happen
inside the caller's write transaction, so the increment is atomic with the work
it guards. There is no background cleanup in v1 — old window rows are harmless.
"""

from datetime import datetime, timedelta

from fastapi import Request
from sqlalchemy.orm import Session

from app import errors
from app.models.rate_limit import RateLimitBucket
from app.util import utcnow

_EPOCH = datetime(1970, 1, 1)


def _window_start(now: datetime, window_seconds: int) -> datetime:
    elapsed = (now - _EPOCH).total_seconds()
    floored = (int(elapsed) // window_seconds) * window_seconds
    return _EPOCH + timedelta(seconds=floored)


def enforce(
    db: Session,
    *,
    scope: str,
    bucket: str,
    limit: int,
    window_seconds: int,
    amount: int = 1,
) -> None:
    """Reserve ``amount`` against (scope, bucket); raise 429 if it would exceed."""
    window_start = _window_start(utcnow(), window_seconds)
    row = db.get(RateLimitBucket, (scope, bucket, window_start))
    if row is None:
        row = RateLimitBucket(scope=scope, bucket=bucket, window_start=window_start, count=0)
        db.add(row)
    if row.count + amount > limit:
        raise errors.rate_limit_exceeded()
    row.count += amount


def client_ip(request: Request) -> str:
    """Real visitor IP.

    Cloudflare sits in front of EC2, so the per-IP bucket must read
    ``CF-Connecting-IP``; without it every request would share Cloudflare's edge
    IP. Falls back to the socket peer for local/dev.
    """
    cf_ip = request.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    return request.client.host if request.client else "unknown"
