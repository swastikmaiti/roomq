"""Agenda update schema (endpoint 5c)."""

from pydantic import BaseModel


class AgendaRequest(BaseModel):
    agenda: str


class AgendaResponse(BaseModel):
    status: str = "ok"
    agenda: str
