"""Endpoint 1 — create a room (no auth)."""

from datetime import timedelta

from fastapi import APIRouter, Request
from sqlalchemy.orm import Session

from app import errors
from app.config import get_settings
from app.models.room import Room
from app.schemas.room import CreateRoomRequest, CreateRoomResponse
from app.services import ids, rate_limit
from app.services.db import run_write
from app.util import iso, utcnow

router = APIRouter()
settings = get_settings()


@router.post("/rooms", response_model=CreateRoomResponse)
def create_room(body: CreateRoomRequest, request: Request) -> CreateRoomResponse:
    minutes = (
        body.active_for_minutes
        if body.active_for_minutes is not None
        else settings.default_room_minutes
    )
    if not settings.min_room_minutes <= minutes <= settings.max_room_minutes:
        raise errors.invalid_duration()

    agenda = (body.agenda or "").strip()[: settings.max_agenda_chars] or None
    ip = rate_limit.client_ip(request)

    def work(db: Session) -> Room:
        rate_limit.enforce(
            db,
            scope=f"ip:{ip}",
            bucket="room_create",
            limit=settings.limit_ip_rooms_per_day,
            window_seconds=86_400,
        )
        room = Room(
            room_id=ids.new_room_id(),
            agenda=agenda,
            expires_at=utcnow() + timedelta(minutes=minutes),
        )
        db.add(room)
        return room

    room = run_write(work)

    room_link = f"{settings.api_base_url}/rooms/{room.room_id}"
    expires_at = iso(room.expires_at)
    return CreateRoomResponse(
        room_id=room.room_id,
        viewer_link=f"{settings.ui_base_url}/rooms/{room.room_id}",
        room_link=room_link,
        agenda=room.agenda,
        expires_at=expires_at,
    )
