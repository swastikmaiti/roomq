"""Room model.

The ``room_id`` is the primary key *and* the room's only access secret. The
``ended`` state is computed (``now() > expires_at``), never stored — there is no
``ended_at`` column and no purge job.
"""

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.util import utcnow


class Room(Base):
    __tablename__ = "room"

    room_id: Mapped[str] = mapped_column(String, primary_key=True)
    agenda: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    agents: Mapped[list["Agent"]] = relationship(  # noqa: F821
        back_populates="room", order_by="Agent.joined_at"
    )

    def is_ended(self, *, at: datetime | None = None) -> bool:
        return (at or utcnow()) > self.expires_at
