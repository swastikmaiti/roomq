"""Admin / moderation endpoints — content takedown.

Gated by the shared admin token (see ``app.auth.admin``); off unless
``ADMIN_TOKEN`` is configured. Deletes are hard (rows are removed, not flagged)
so takedowns actually scrub the live DB. Routes are hidden from the public
OpenAPI schema.

Foreign keys are enforced (SQLite ``foreign_keys=ON``), so rows are removed in
dependency order: message_read → message → agent → room.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app import errors
from app.auth.admin import require_admin
from app.models.agent import Agent
from app.models.message import Message
from app.models.message_read import MessageRead
from app.models.room import Room
from app.services.db import run_write

router = APIRouter(dependencies=[Depends(require_admin)])


@router.delete("/rooms/{room_id}", include_in_schema=False)
def admin_delete_room(room_id: str) -> dict:
    """Hard-delete a room and everything under it (any state, expired or live)."""

    def work(db: Session) -> int:
        if db.get(Room, room_id) is None:
            raise errors.room_not_found()
        msg_ids = select(Message.message_id).where(Message.room_id == room_id)
        db.execute(delete(MessageRead).where(MessageRead.message_id.in_(msg_ids)))
        deleted = db.execute(delete(Message).where(Message.room_id == room_id)).rowcount
        db.execute(delete(Agent).where(Agent.room_id == room_id))
        db.execute(delete(Room).where(Room.room_id == room_id))
        return deleted or 0

    deleted = run_write(work)
    return {"status": "deleted", "room_id": room_id, "messages_deleted": deleted}


@router.delete("/rooms/{room_id}/messages/{message_id}", include_in_schema=False)
def admin_delete_message(room_id: str, message_id: str) -> dict:
    """Hard-delete a single message (and its read receipts) from a room."""

    def work(db: Session) -> None:
        msg = db.execute(
            select(Message).where(
                Message.message_id == message_id, Message.room_id == room_id
            )
        ).scalar_one_or_none()
        if msg is None:
            raise errors.message_not_found()
        db.execute(delete(MessageRead).where(MessageRead.message_id == message_id))
        db.execute(delete(Message).where(Message.message_id == message_id))

    run_write(work)
    return {"status": "deleted", "message_id": message_id}
