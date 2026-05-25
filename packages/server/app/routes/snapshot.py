"""Endpoint 11 — UI snapshot (no auth; the session id is the secret).

A pure DB read that works while the room is live and after it has ended. The
viewer polls this with the last message id it has seen as ``since``.
"""

from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import serialize
from app.config import get_settings
from app.database import get_db
from app.models.agent import Agent
from app.models.message import Message
from app.models.message_read import MessageRead
from app.models.room import Room
from app.schemas.snapshot import SnapshotMessage, SnapshotResponse
from app.services.expiry import get_room
from app.util import iso

router = APIRouter()
settings = get_settings()


@router.get("/rooms/{room_id}/snapshot", response_model=SnapshotResponse)
def snapshot(
    since: str | None = Query(default=None),
    limit: int = Query(default=200, ge=1, le=1000),
    room: Room = Depends(get_room),
    db: Session = Depends(get_db),
) -> SnapshotResponse:
    # Resolve the opaque cursor to its ordering key.
    since_id = 0
    if since:
        found = db.scalar(
            select(Message.id).where(
                Message.message_id == since, Message.room_id == room.room_id
            )
        )
        if found:
            since_id = found

    messages = list(
        db.scalars(
            select(Message)
            .where(Message.room_id == room.room_id, Message.id > since_id)
            .order_by(Message.id)
            .limit(limit)
        ).all()
    )

    reads_by_msg: dict[str, list[str]] = defaultdict(list)
    if messages:
        msg_ids = [m.message_id for m in messages]
        for mid, aid in db.execute(
            select(MessageRead.message_id, MessageRead.agent_id).where(
                MessageRead.message_id.in_(msg_ids),
                MessageRead.read_at.is_not(None),
            )
        ).all():
            reads_by_msg[mid].append(aid)

    names = serialize.name_map(db, room.room_id)
    agents = db.scalars(
        select(Agent).where(Agent.room_id == room.room_id).order_by(Agent.joined_at)
    ).all()

    # room_link is the agent-facing API host; the viewer builds the copy-curl
    # bundles from it client-side.
    expires_at = iso(room.expires_at)
    room_link = f"{settings.api_base_url}/rooms/{room.room_id}"

    return SnapshotResponse(
        status=serialize.room_status(room),
        agenda=room.agenda,
        expires_at=expires_at,
        seconds_remaining=serialize.seconds_remaining(room),
        room_link=room_link,
        agents=serialize.roster_entries(list(agents)),
        messages=[
            SnapshotMessage(
                msg_id=m.message_id,
                from_agent_id=m.from_agent_id,
                from_name=names.get(m.from_agent_id, "System"),
                to=m.to_targets,
                content=m.content,
                in_reply_to=m.in_reply_to_message_id,
                kind=m.kind,
                broadcast=m.is_broadcast,
                sent_at=iso(m.sent_at),
                read_by=reads_by_msg.get(m.message_id, []),
            )
            for m in messages
        ],
    )
