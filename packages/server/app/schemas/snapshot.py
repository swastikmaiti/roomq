"""UI snapshot schema (endpoint 11).

Public read endpoint that powers the conversation viewer. Each message carries
``read_by`` (agent ids that have read it) so the UI can render per-message read
indicators; this is what closes the snapshot read-state gap noted in the plan.
"""

from pydantic import BaseModel

from app.schemas.common import RosterEntry


class SnapshotMessage(BaseModel):
    msg_id: str
    from_agent_id: str | None  # null for system messages
    from_name: str
    to: list[str]  # agent ids, or ["all"] for a broadcast
    content: str
    in_reply_to: str | None
    kind: str  # "user" | "system"
    broadcast: bool
    sent_at: str
    read_by: list[str]


class SnapshotResponse(BaseModel):
    status: str  # "live" | "ended"
    agenda: str | None
    expires_at: str
    seconds_remaining: int
    room_link: str  # agent-facing API host
    agents: list[RosterEntry]
    messages: list[SnapshotMessage]
