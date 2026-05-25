"""Endpoint 5b — leave the room.

Atomically marks the agent ``left``, stamps ``left_at``, and clears the token
hash (killing the token). Calling again returns ``410 agent_left_room`` because
the auth dependency now rejects the dead token.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.agent_token import get_current_agent
from app.models.agent import STATUS_LEFT, Agent
from app.services.db import run_write
from app.util import utcnow

router = APIRouter()


@router.post("/rooms/{room_id}/leave")
def leave_room(agent: Agent = Depends(get_current_agent)) -> dict:
    def work(db: Session) -> None:
        row = db.get(Agent, agent.agent_id)
        row.status = STATUS_LEFT
        row.left_at = utcnow()
        row.token_hash = None

    run_write(work)
    return {"status": "left"}
