"""Messaging schemas (endpoints 4, 5, 10).

Some fields are "present only when relevant" per the plan: ``broadcast`` and
``kind`` on an inbox message, ``status`` on an inbox response, and
``left_agents`` on a send response are omitted entirely when not applicable
(via ``@model_serializer``). ``in_reply_to`` is always present (null or a value).
"""

from pydantic import BaseModel, model_serializer

from app.schemas.common import LeftAgentRef


# --- Send (5) -----------------------------------------------------------
class OutgoingMessage(BaseModel):
    # to: a single agent_id, a list of agent_ids, or the literal "all".
    # The primary (first-registered) agent must set it. Secondary agents may omit
    # it — the server routes their messages to the primary regardless.
    to: str | list[str] | None = None
    content: str
    # Required on every entry: null (new topic) or the msg_id being answered.
    in_reply_to: str | None


class SendMessageRequest(BaseModel):
    messages: list[OutgoingMessage]


class SendMessageResponse(BaseModel):
    status: str = "ok"
    # Present only when a direct recipient had already left the room.
    left_agents: list[LeftAgentRef] | None = None

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        data = handler(self)
        if self.left_agents is None:
            data.pop("left_agents", None)
        return data


# --- Inbox (4) ----------------------------------------------------------
class InboxMessage(BaseModel):
    msg_id: str
    agent_id: str  # sender ("system" for room events)
    agent_name: str
    content: str
    in_reply_to: str | None = None
    broadcast: bool | None = None  # present only when true
    kind: str | None = None  # present only for "system"

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        data = handler(self)
        if self.broadcast is None:
            data.pop("broadcast", None)
        if self.kind is None:
            data.pop("kind", None)
        return data


class InboxResponse(BaseModel):
    messages: list[InboxMessage]
    status: str | None = None  # "no_new_messages" when empty

    @model_serializer(mode="wrap")
    def _serialize(self, handler):
        data = handler(self)
        if self.status is None:
            data.pop("status", None)
        return data


# --- Read receipts (10) -------------------------------------------------
class ReadReceipt(BaseModel):
    agent_id: str
    name: str
    read_at: str | None  # null until that recipient first polled


class ReadReceiptsResponse(BaseModel):
    message_id: str
    reads: list[ReadReceipt]
