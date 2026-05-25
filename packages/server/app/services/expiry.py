"""Room-loading and expiry dependencies.

``get_room`` loads a room or raises ``404 room_not_found`` — used by every
room-scoped route (including the post-expiry snapshot/transcript readers).
``require_live_room`` additionally raises ``410 room_expired`` once
``now() > expires_at``; the room is never deleted, so the readers still work.
"""

from fastapi import Depends, Path
from sqlalchemy.orm import Session

from app import errors
from app.database import get_db
from app.models.room import Room


def get_room(
    room_id: str = Path(...),
    db: Session = Depends(get_db),
) -> Room:
    room = db.get(Room, room_id)
    if room is None:
        raise errors.room_not_found()
    return room


def require_live_room(room: Room = Depends(get_room)) -> Room:
    if room.is_ended():
        raise errors.room_expired()
    return room
