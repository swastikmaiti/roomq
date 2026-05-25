"""Endpoints 2 (register) and 3 (room_info)."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import errors, serialize
from app.auth.agent_token import build_token, get_current_agent, hash_secret
from app.config import get_settings
from app.database import get_db
from app.models.agent import STATUS_ACTIVE, Agent
from app.models.room import Room
from app.schemas.agent import RegisterRequest, RegisterResponse, RoomInfoResponse
from app.services import ids
from app.services.db import run_write
from app.services.expiry import require_live_room
from app.util import iso

router = APIRouter()
settings = get_settings()


def _resolve_name(name: str, taken: set[str]) -> str:
    """Append -2, -3, … until the name is unique within the room."""
    if name not in taken:
        return name
    n = 2
    while f"{name}-{n}" in taken:
        n += 1
    return f"{name}-{n}"


@router.post("/rooms/{room_id}/register", response_model=RegisterResponse)
def register_agent(
    body: RegisterRequest,
    room: Room = Depends(require_live_room),
) -> RegisterResponse:
    def work(db: Session) -> tuple[Agent, str]:
        agents = db.scalars(
            select(Agent).where(Agent.room_id == room.room_id)
        ).all()
        active = [a for a in agents if a.status == STATUS_ACTIVE]
        if len(active) >= settings.max_agents_per_room:
            raise errors.room_full()

        name = _resolve_name(body.name, {a.name for a in agents})
        secret = ids.new_token_secret()
        agent = Agent(
            agent_id=ids.new_agent_id(),
            room_id=room.room_id,
            name=name,
            token_hash=hash_secret(secret),
            status=STATUS_ACTIVE,
            description=body.description,
        )
        db.add(agent)
        db.flush()
        return agent, build_token(agent.agent_id, secret)

    agent, token = run_write(work)

    # Joining returns only the identity + token; the human drives everything else
    # via the copy-curl bundles in the viewer.
    return RegisterResponse(
        status="ok",
        agent_id=agent.agent_id,
        name=agent.name,
        token=token,
    )


@router.get("/rooms/{room_id}/room_info", response_model=RoomInfoResponse)
def room_info(
    _agent: Agent = Depends(get_current_agent),
    room: Room = Depends(require_live_room),
    db: Session = Depends(get_db),
) -> RoomInfoResponse:
    agents = db.scalars(
        select(Agent).where(Agent.room_id == room.room_id).order_by(Agent.joined_at)
    ).all()
    return RoomInfoResponse(
        status=serialize.room_status(room),
        agenda=room.agenda,
        expires_at=iso(room.expires_at),
        seconds_remaining=serialize.seconds_remaining(room),
        agents=serialize.roster_entries(list(agents)),
    )
