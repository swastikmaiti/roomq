"""SQLAlchemy models.

Importing this package registers every model on ``Base.metadata`` (needed by
Alembic autogenerate and by ``Base.metadata.create_all`` in tests).
"""

from app.models.agent import Agent
from app.models.message import Message
from app.models.message_read import MessageRead
from app.models.rate_limit import RateLimitBucket
from app.models.room import Room

__all__ = ["Agent", "Message", "MessageRead", "RateLimitBucket", "Room"]
