"""Endpoint 5c — update the shared agenda.

Any active agent may edit (last writer wins, capped at 200 chars). The change is
atomic: it replaces ``Room.agenda``, inserts a system broadcast into every other
active agent's inbox, and persists that system message to the transcript. The
updater does not receive the broadcast; agents who join later don't get it.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.agent_token import get_current_agent
from app.config import get_settings
from app.models.agent import STATUS_ACTIVE, Agent
from app.models.message import KIND_SYSTEM, Message
from app.models.message_read import MessageRead
from app.models.room import Room
from app.schemas.agenda import AgendaRequest, AgendaResponse
from app.services import ids, rate_limit
from app.services.db import run_write
from app.util import utcnow

router = APIRouter()
settings = get_settings()


@router.post("/rooms/{room_id}/agenda", response_model=AgendaResponse)
def update_agenda(
    body: AgendaRequest,
    agent: Agent = Depends(get_current_agent),
) -> AgendaResponse:
    new_agenda = body.agenda.strip()[: settings.max_agenda_chars]

    def work(db: Session) -> str:
        rate_limit.enforce(
            db,
            scope=f"room:{agent.room_id}",
            bucket="agenda_update",
            limit=settings.limit_room_agenda_per_min,
            window_seconds=60,
        )
        room = db.get(Room, agent.room_id)
        room.agenda = new_agenda

        message = Message(
            message_id=ids.new_message_id(),
            room_id=agent.room_id,
            from_agent_id=None,
            kind=KIND_SYSTEM,
            to_targets=["all"],
            in_reply_to_message_id=None,
            content=f'Agenda updated by {agent.name} ({agent.agent_id}): "{new_agenda}"',
            sent_at=utcnow(),
        )
        db.add(message)
        db.flush()

        others = db.scalars(
            select(Agent.agent_id).where(
                Agent.room_id == agent.room_id,
                Agent.status == STATUS_ACTIVE,
                Agent.agent_id != agent.agent_id,
            )
        ).all()
        for aid in others:
            db.add(MessageRead(message_id=message.message_id, agent_id=aid))
        return room.agenda

    agenda = run_write(work)
    return AgendaResponse(status="ok", agenda=agenda)
