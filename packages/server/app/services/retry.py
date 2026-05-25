"""IO retry policy.

Per the project's IO-retry standard, every IO-bound operation is wrapped with
exponential backoff and **at most 2 retries** (3 attempts total), so transient
failures such as SQLite's ``database is locked`` self-heal instead of surfacing
as 500s. Only ``OperationalError`` (the transient class) is retried; integrity
and programming errors fail fast.
"""

from sqlalchemy.exc import OperationalError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

io_retry = retry(
    retry=retry_if_exception_type(OperationalError),
    wait=wait_exponential(multiplier=0.1, max=1.0),
    stop=stop_after_attempt(3),  # 1 initial attempt + 2 retries
    reraise=True,
)
