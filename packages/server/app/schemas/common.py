"""Shared response fragments."""

from pydantic import BaseModel


class RosterEntry(BaseModel):
    agent_id: str
    name: str
    status: str  # "active" | "left"
    # Self-advertised details so other agents (and the human viewer) can tell who
    # is who and pick recipients. description is required at registration; the
    # tag lists are free-form and may be null.
    description: str | None = None
    skills: list[str] | None = None
    capabilities: list[str] | None = None


class LeftAgentRef(BaseModel):
    agent_id: str
    name: str
