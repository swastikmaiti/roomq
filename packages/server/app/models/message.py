"""Message model.

Implementation note: the public identifier is the string ``message_id``, but the
table also carries a surrogate autoincrement integer ``id`` used purely for
stable ordering and cursor pagination (``GET /snapshot?since=<message_id>``
resolves the cursor to its ``id`` and returns rows with a greater ``id``).
SQLite has no non-PK autoincrement, so the integer is the primary key while
``message_id`` stays unique and is what every API surface exposes.

``kind='system'`` rows (e.g. agenda-change notices) have ``from_agent_id=None``.
``to_targets`` is a JSON list of agent ids, or the single-element list ``["all"]``
for a broadcast.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.util import utcnow

KIND_USER = "user"
KIND_SYSTEM = "system"


class Message(Base):
    __tablename__ = "message"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    message_id: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    room_id: Mapped[str] = mapped_column(ForeignKey("room.room_id"), index=True, nullable=False)
    from_agent_id: Mapped[str | None] = mapped_column(
        ForeignKey("agent.agent_id"), nullable=True
    )
    kind: Mapped[str] = mapped_column(String, default=KIND_USER, nullable=False)
    to_targets: Mapped[list] = mapped_column(JSON, nullable=False)
    in_reply_to_message_id: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    @property
    def is_broadcast(self) -> bool:
        return self.to_targets == ["all"]
