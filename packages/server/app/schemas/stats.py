"""Public aggregate stats shown on the landing page."""

from pydantic import BaseModel


class StatsResponse(BaseModel):
    total_sessions: int  # rooms ever created (nothing is purged)
    active_sessions: int  # rooms not yet expired
    active_agents: int  # active agents currently in a live room
