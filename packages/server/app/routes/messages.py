"""Endpoints 4 (poll), 4w (wait/long-poll), 5 (batch send), 10 (read receipts)."""

import asyncio
import time
from datetime import datetime

from fastapi import APIRouter, Depends, Header, Path
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import errors, serialize
from app.auth.agent_token import authenticate_agent, get_current_agent
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models.agent import STATUS_ACTIVE, Agent
from app.models.message import KIND_SYSTEM, KIND_USER, Message
from app.models.message_read import MessageRead
from app.models.room import Room
from app.schemas.common import LeftAgentRef
from app.schemas.message import (
    InboxMessage,
    InboxResponse,
    ReadReceipt,
    ReadReceiptsResponse,
    SendMessageRequest,
    SendMessageResponse,
)
from app.services import ids, rate_limit
from app.services.db import run_write
from app.util import iso, utcnow

router = APIRouter()
settings = get_settings()

SYSTEM_SENTINEL = "system"
ALL = "all"


# --- Endpoint 4: poll ---------------------------------------------------
def _drain_inbox(db: Session, agent_id: str, room_id: str) -> list[InboxMessage]:
    """Return the caller's unread messages (oldest-first) and mark them read."""
    rows = db.execute(
        select(Message, MessageRead)
        .join(MessageRead, MessageRead.message_id == Message.message_id)
        .where(
            MessageRead.agent_id == agent_id,
            MessageRead.read_at.is_(None),
        )
        .order_by(Message.id)
    ).all()

    names = serialize.name_map(db, room_id)
    now = utcnow()
    out: list[InboxMessage] = []
    for msg, read in rows:
        read.read_at = now
        is_system = msg.kind == KIND_SYSTEM
        out.append(
            InboxMessage(
                msg_id=msg.message_id,
                agent_id=msg.from_agent_id or SYSTEM_SENTINEL,
                agent_name=names.get(msg.from_agent_id, "System"),
                content=msg.content,
                in_reply_to=msg.in_reply_to_message_id,
                broadcast=True if msg.is_broadcast else None,
                kind=KIND_SYSTEM if is_system else None,
            )
        )
    return out


@router.get("/rooms/{room_id}/messages", response_model=InboxResponse)
def poll_messages(agent: Agent = Depends(get_current_agent)) -> InboxResponse:
    """Return all unread messages addressed to the caller, oldest-first, and
    mark them read in the same transaction."""
    messages = run_write(lambda db: _drain_inbox(db, agent.agent_id, agent.room_id))
    return InboxResponse(
        messages=messages,
        status=None if messages else "no_new_messages",
    )


# --- Endpoint 4w: wait (long-poll) --------------------------------------
def _authenticate_wait(room_id: str, authorization: str | None) -> tuple[str, datetime]:
    """One-shot auth for the long-poll on a short-lived session.

    Returns ``(agent_id, room_expires_at)``. Mirrors the ``get_current_agent``
    chain (``room_not_found`` / ``room_expired`` / ``invalid_token`` /
    ``agent_left_room``) but releases the session immediately so a held poll
    doesn't pin a connection open for its whole duration.
    """
    db = SessionLocal()
    try:
        room = db.get(Room, room_id)
        if room is None:
            raise errors.room_not_found()
        if room.is_ended():
            raise errors.room_expired()
        agent = authenticate_agent(db, room, authorization)
        return agent.agent_id, room.expires_at
    finally:
        db.close()


@router.get("/rooms/{room_id}/wait", response_model=InboxResponse)
async def wait_messages(
    room_id: str = Path(...),
    authorization: str | None = Header(default=None),
) -> InboxResponse:
    """Long-poll: hold the connection open until the caller has a message, then
    return it (marked read) — same shape as ``GET /messages``.

    Returns an empty ``no_new_messages`` after ``wait_max_seconds`` (kept under
    Cloudflare's origin timeout) so the client reconnects to keep waiting. The
    handler is async and checks on its own short-lived sessions, so a waiting
    request ties up neither a worker thread nor a DB connection while idle.
    """
    agent_id, room_expires_at = await run_in_threadpool(
        _authenticate_wait, room_id, authorization
    )

    # Stop at the cap or the room's end, whichever comes first.
    room_remaining = (room_expires_at - utcnow()).total_seconds()
    deadline = time.monotonic() + min(settings.wait_max_seconds, max(0.0, room_remaining))

    while True:
        messages = await run_in_threadpool(
            lambda: run_write(lambda db: _drain_inbox(db, agent_id, room_id))
        )
        if messages:
            return InboxResponse(messages=messages, status=None)
        if time.monotonic() >= deadline:
            return InboxResponse(messages=[], status="no_new_messages")
        await asyncio.sleep(settings.wait_poll_interval_seconds)


# --- Endpoint 5: batch send ---------------------------------------------
def _normalize_targets(to: str | list[str]) -> tuple[bool, list[str]]:
    """Return (is_broadcast, explicit_ids). Raises on the system sentinel."""
    if isinstance(to, str):
        if to == ALL:
            return True, []
        ids_ = [to]
    else:
        ids_ = list(to)
    if SYSTEM_SENTINEL in ids_:
        raise errors.invalid_recipient()
    return False, ids_


@router.post("/rooms/{room_id}/messages", response_model=SendMessageResponse)
def send_messages(
    body: SendMessageRequest,
    agent: Agent = Depends(get_current_agent),
) -> SendMessageResponse:
    batch = body.messages
    if not batch or len(batch) > settings.max_batch_size:
        raise errors.payload_too_large()
    for item in batch:
        if len(item.content.encode("utf-8")) > settings.max_content_bytes:
            raise errors.payload_too_large()
        # Validate the system sentinel up front (before any write) when a
        # recipient is given. Secondary agents may omit `to` entirely.
        if item.to is not None:
            _normalize_targets(item.to)

    def work(db: Session) -> dict[str, LeftAgentRef]:
        rate_limit.enforce(
            db,
            scope=f"agent:{agent.agent_id}",
            bucket="msg_send",
            limit=settings.limit_agent_msgs_per_min,
            window_seconds=60,
            amount=len(batch),
        )
        rate_limit.enforce(
            db,
            scope=f"room:{agent.room_id}",
            bucket="msg_send",
            limit=settings.limit_room_msgs_per_min,
            window_seconds=60,
            amount=len(batch),
        )

        agents = {
            a.agent_id: a
            for a in db.scalars(
                select(Agent).where(Agent.room_id == agent.room_id)
            ).all()
        }
        # The primary is the first agent to register; everyone after is a
        # secondary. Secondaries can only message the primary, so the server
        # routes their messages there — ignoring (or not needing) a `to`.
        primary = min(agents.values(), key=lambda a: (a.joined_at, a.agent_id))
        sender_is_secondary = agent.agent_id != primary.agent_id
        active_others = [
            aid
            for aid, a in agents.items()
            if a.status == STATUS_ACTIVE and aid != agent.agent_id
        ]

        left_agents: dict[str, LeftAgentRef] = {}
        now = utcnow()

        for item in batch:
            if sender_is_secondary:
                # Forced route to the primary; any provided `to` is ignored.
                to_targets = [primary.agent_id]
                if primary.status == STATUS_ACTIVE:
                    recipients = [primary.agent_id]
                else:  # the primary has left the room
                    recipients = []
                    left_agents[primary.agent_id] = LeftAgentRef(
                        agent_id=primary.agent_id, name=primary.name
                    )
            elif item.to is None:
                # The primary must address someone explicitly.
                raise errors.invalid_recipient()
            else:
                is_broadcast, explicit = _normalize_targets(item.to)
                if is_broadcast:
                    recipients = list(active_others)
                    to_targets = [ALL]
                else:
                    recipients = []
                    to_targets = []
                    for aid in explicit:
                        if aid == agent.agent_id:  # server drops the sender
                            continue
                        target = agents.get(aid)
                        if target is None:  # unknown id — silently ignored
                            continue
                        to_targets.append(aid)
                        if target.status == STATUS_ACTIVE:
                            recipients.append(aid)
                        else:  # addressed an agent that already left
                            left_agents[aid] = LeftAgentRef(agent_id=aid, name=target.name)

            message = Message(
                message_id=ids.new_message_id(),
                room_id=agent.room_id,
                from_agent_id=agent.agent_id,
                kind=KIND_USER,
                to_targets=to_targets,
                in_reply_to_message_id=item.in_reply_to,
                content=item.content,
                sent_at=now,
            )
            db.add(message)
            for aid in dict.fromkeys(recipients):  # de-dupe, preserve order
                db.add(MessageRead(message_id=message.message_id, agent_id=aid))

        return left_agents

    left = run_write(work)
    return SendMessageResponse(
        status="ok",
        left_agents=list(left.values()) or None,
    )


# --- Endpoint 10: read receipts (sender only) ---------------------------
@router.get(
    "/rooms/{room_id}/messages/{message_id}/reads",
    response_model=ReadReceiptsResponse,
)
def read_receipts(
    message_id: str = Path(...),
    agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
) -> ReadReceiptsResponse:
    message = db.scalar(
        select(Message).where(
            Message.message_id == message_id,
            Message.room_id == agent.room_id,
        )
    )
    if message is None or message.from_agent_id != agent.agent_id:
        raise errors.message_not_found()

    names = serialize.name_map(db, agent.room_id)
    reads = db.scalars(
        select(MessageRead).where(MessageRead.message_id == message_id)
    ).all()
    return ReadReceiptsResponse(
        message_id=message_id,
        reads=[
            ReadReceipt(
                agent_id=r.agent_id,
                name=names.get(r.agent_id, r.agent_id),
                read_at=iso(r.read_at),
            )
            for r in reads
        ],
    )
