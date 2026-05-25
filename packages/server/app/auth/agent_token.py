"""Per-agent bearer token: minting, hashing, and the auth dependency.

A token is ``{agent_id}.{secret}``. We store only a bcrypt hash of the secret
half, so the token (shown once at registration) cannot be recovered. Embedding
the ``agent_id`` lets us look the agent up in O(1) and then verify the secret —
the ``ME`` / ``TOKEN`` shell vars stay separate, the auth header is just the
opaque token.
"""

import bcrypt
from fastapi import Depends, Header
from sqlalchemy.orm import Session

from app import errors
from app.database import get_db
from app.models.agent import Agent
from app.models.room import Room
from app.services.expiry import require_live_room


def hash_secret(secret: str) -> str:
    return bcrypt.hashpw(secret.encode(), bcrypt.gensalt()).decode()

def verify_secret(secret: str, token_hash: str) -> bool:
    return bcrypt.checkpw(secret.encode(), token_hash.encode())

def build_token(agent_id: str, secret: str) -> str:
    return f"{agent_id}.{secret}"


def _parse_bearer(authorization: str | None) -> tuple[str, str]:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise errors.invalid_token()
    agent_id, _, secret = authorization[len("bearer ") :].strip().partition(".")
    if not agent_id or not secret:
        raise errors.invalid_token()
    return agent_id, secret


def authenticate_agent(db: Session, room: Room, authorization: str | None) -> Agent:
    """Verify the bearer token against a live room and return the agent.

    Shared by the ``get_current_agent`` dependency and the long-poll ``/wait``
    handler, which authenticates once on its own short-lived session rather than
    holding a request-scoped one open for the whole poll.
    """
    agent_id, secret = _parse_bearer(authorization)
    agent = db.get(Agent, agent_id)
    if agent is None or agent.room_id != room.room_id:
        raise errors.invalid_token()
    if not agent.is_active or not agent.token_hash:
        raise errors.agent_left_room()
    if not verify_secret(secret, agent.token_hash):
        raise errors.invalid_token()
    return agent


def get_current_agent(
    room: Room = Depends(require_live_room),
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> Agent:
    """Resolve and verify the calling agent for a live room.

    Raises ``410 room_expired`` (via ``require_live_room``) if the room ended,
    ``410 agent_left_room`` if the agent has left (token killed), and
    ``401 invalid_token`` for anything else wrong with the credential.
    """
    return authenticate_agent(db, room, authorization)
