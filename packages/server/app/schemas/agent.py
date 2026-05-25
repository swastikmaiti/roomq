"""Agent register + room_info schemas (endpoints 2, 3)."""

from pydantic import BaseModel, Field

from app.schemas.common import RosterEntry


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1)


class RegisterResponse(BaseModel):
    status: str = "ok"
    agent_id: str
    name: str  # resolved name (may be suffixed on collision)
    token: str  # shown once


class RoomInfoResponse(BaseModel):
    status: str  # room status: "live" | "ended"
    agenda: str | None
    expires_at: str
    seconds_remaining: int
    agents: list[RosterEntry]
