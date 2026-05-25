"""Endpoint — public aggregate stats for the landing page (no auth).

Three cheap COUNTs: total rooms ever, rooms still live, and active agents in
live rooms. Read-only, so it uses the request-scoped session.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.agent import STATUS_ACTIVE, Agent
from app.models.room import Room
from app.schemas.stats import StatsResponse
from app.util import utcnow

router = APIRouter()


@router.get("/stats", response_model=StatsResponse)
def stats(db: Session = Depends(get_db)) -> StatsResponse:
    now = utcnow()
    total = db.scalar(select(func.count()).select_from(Room)) or 0
    active = db.scalar(
        select(func.count()).select_from(Room).where(Room.expires_at > now)
    ) or 0
    active_agents = db.scalar(
        select(func.count())
        .select_from(Agent)
        .join(Room, Agent.room_id == Room.room_id)
        .where(Agent.status == STATUS_ACTIVE, Room.expires_at > now)
    ) or 0
    return StatsResponse(
        total_sessions=total, active_sessions=active, active_agents=active_agents
    )
