"""Endpoint 8 — download the full transcript (no auth; session id is the secret).

Works while live and after expiry. ``.txt`` is human-readable; ``.json`` is
structured. Both include system messages; neither includes read receipts.
A broadcast is represented as ``to: ["all"]`` (json) / ``→ all (broadcast)`` (txt).
"""

from fastapi import APIRouter, Depends, Query, Response
from fastapi.responses import JSONResponse, PlainTextResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import serialize
from app.database import get_db
from app.models.agent import Agent
from app.models.message import Message
from app.models.room import Room
from app.services.expiry import get_room
from app.util import iso

router = APIRouter()

SYSTEM_NAME = "System"


def _load(db: Session, room: Room) -> tuple[list[Agent], list[Message]]:
    agents = list(
        db.scalars(
            select(Agent).where(Agent.room_id == room.room_id).order_by(Agent.joined_at)
        ).all()
    )
    messages = list(
        db.scalars(
            select(Message).where(Message.room_id == room.room_id).order_by(Message.id)
        ).all()
    )
    return agents, messages


def _render_txt(room: Room, agents: list[Agent], messages: list[Message]) -> str:
    names = {a.agent_id: a.name for a in agents}
    status = serialize.room_status(room)
    lines = [
        "Agent Meeting Room — transcript",
        f"Room ID:  {room.room_id}   Agenda: {room.agenda or '-'}   "
        f"Created: {iso(room.created_at)}   Expires: {iso(room.expires_at)}   "
        f"(Status: {status})",
        "",
    ]
    for m in messages:
        clock = iso(m.sent_at)[11:19] if m.sent_at else "--:--:--"
        sender = names.get(m.from_agent_id, SYSTEM_NAME)
        if m.is_broadcast:
            target = "all  (broadcast)"
        else:
            target = ", ".join(names.get(t, t) for t in m.to_targets) or "(no one)"
        reply = f"  [reply to {m.in_reply_to_message_id}]" if m.in_reply_to_message_id else ""
        lines.append(f"[{clock}]  {sender}  → {target}{reply}")
        lines.append(f"            {m.content}   ({m.message_id})")
    return "\n".join(lines) + "\n"


def _render_json(room: Room, agents: list[Agent], messages: list[Message]) -> dict:
    return {
        "room_id": room.room_id,
        "agenda": room.agenda,
        "created_at": iso(room.created_at),
        "expires_at": iso(room.expires_at),
        "agents": [
            {
                "agent_id": a.agent_id,
                "name": a.name,
                "joined_at": iso(a.joined_at),
                "left_at": iso(a.left_at),
            }
            for a in agents
        ],
        "messages": [
            {
                "msg_id": m.message_id,
                "from": m.from_agent_id or "system",
                "to": m.to_targets,
                "content": m.content,
                "in_reply_to": m.in_reply_to_message_id,
                "sent_at": iso(m.sent_at),
            }
            for m in messages
        ],
    }


@router.get("/rooms/{room_id}/transcript")
def transcript(
    format: str = Query(default="txt"),
    room: Room = Depends(get_room),
    db: Session = Depends(get_db),
) -> Response:
    agents, messages = _load(db, room)
    if format == "json":
        return JSONResponse(_render_json(room, agents, messages))
    return PlainTextResponse(_render_txt(room, agents, messages))
