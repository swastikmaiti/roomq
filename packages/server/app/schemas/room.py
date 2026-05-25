"""Room create schemas (endpoint 1)."""

from pydantic import BaseModel


class CreateRoomRequest(BaseModel):
    # Validated in the route so out-of-range values return 400 invalid_duration
    # (a bare Pydantic constraint would surface as 422). None -> server default.
    active_for_minutes: int | None = None
    agenda: str | None = None


class CreateRoomResponse(BaseModel):
    room_id: str
    viewer_link: str  # human host: {ui_base_url}/rooms/{id}
    room_link: str  # agent host:  {api_base_url}/rooms/{id}
    agenda: str | None
    expires_at: str
