"""Fixed-window rate-limit counters.

One row per (scope, bucket, window_start). ``scope`` is e.g. ``ip:1.2.3.4``,
``agent:agt-xxx`` or ``room:abc-123``; ``bucket`` is the action being limited
(``room_create`` / ``msg_send`` / ``agenda_update``). See ``services/rate_limit.py``.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class RateLimitBucket(Base):
    __tablename__ = "rate_limit_bucket"

    scope: Mapped[str] = mapped_column(String, primary_key=True)
    bucket: Mapped[str] = mapped_column(String, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime, primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
