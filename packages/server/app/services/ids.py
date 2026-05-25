"""Identifier and token-secret generators.

The room id doubles as the room's access secret, so it must be high-entropy and
unguessable (~128 bits). The other ids are opaque, prefixed for readability.
"""

import secrets


def new_room_id() -> str:
    """~128-bit URL-safe id; also the room's only access secret."""
    return secrets.token_urlsafe(16)


def new_agent_id() -> str:
    return "agt-" + secrets.token_urlsafe(6)


def new_message_id() -> str:
    return "msg-" + secrets.token_urlsafe(8)


def new_token_secret() -> str:
    """The per-agent secret half of a bearer token (hashed at rest)."""
    return secrets.token_urlsafe(24)
