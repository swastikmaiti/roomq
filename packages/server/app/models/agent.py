"""Agent model.

An agent's bearer token is ``{agent_id}.{secret}``; only a bcrypt hash of the
secret half is stored. ``status`` flips to ``left`` on ``POST /leave`` and the
hash is cleared, which kills the token.
"""

from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.util import utcnow

STATUS_ACTIVE = "active"
STATUS_LEFT = "left"


class Agent(Base):
    __tablename__ = "agent"

    agent_id: Mapped[str] = mapped_column(String, primary_key=True)
    room_id: Mapped[str] = mapped_column(ForeignKey("room.room_id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    token_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default=STATUS_ACTIVE, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    capabilities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    left_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    room: Mapped["Room"] = relationship(back_populates="agents")  # noqa: F821

    @property
    def is_active(self) -> bool:
        return self.status == STATUS_ACTIVE
