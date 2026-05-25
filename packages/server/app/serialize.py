"""Helpers shared by the read-shaped routes (room_info, snapshot, register).

Kept separate so the room-status / roster / countdown logic lives in exactly one
place and the route handlers stay thin.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent import Agent
from app.models.room import Room
from app.schemas.common import RosterEntry
from app.util import utcnow


def room_status(room: Room) -> str:
    return "ended" if room.is_ended() else "live"


def seconds_remaining(room: Room) -> int:
    return max(0, int((room.expires_at - utcnow()).total_seconds()))


def roster_entries(agents: list[Agent]) -> list[RosterEntry]:
    return [
        RosterEntry(
            agent_id=a.agent_id,
            name=a.name,
            status=a.status,
            description=a.description,
            skills=a.skills,
            capabilities=a.capabilities,
        )
        for a in agents
    ]


def name_map(db: Session, room_id: str) -> dict[str, str]:
    """agent_id -> display name for every agent in the room."""
    rows = db.execute(
        select(Agent.agent_id, Agent.name).where(Agent.room_id == room_id)
    ).all()
    return {agent_id: name for agent_id, name in rows}
