"""Per-recipient read tracking.

One row per (message, recipient) is created at send time for every active
recipient except the sender. ``read_at`` is null until the recipient's first
``GET /messages`` picks it up, at which point it is stamped in the same
transaction — so the next poll returns only newer messages.
"""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class MessageRead(Base):
    __tablename__ = "message_read"

    message_id: Mapped[str] = mapped_column(
        ForeignKey("message.message_id"), primary_key=True
    )
    agent_id: Mapped[str] = mapped_column(
        ForeignKey("agent.agent_id"), primary_key=True
    )
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
