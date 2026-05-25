"""Standardized API errors.

Every error is an :class:`APIError` carrying a short machine-readable ``code``.
A single exception handler (registered in ``main.py``) renders them as
``{"error": "<code>"}`` with the right HTTP status, so clients (and the agent
skill's error table) can branch on status + code consistently.
"""

from fastapi import HTTPException


class APIError(HTTPException):
    def __init__(self, status_code: int, code: str) -> None:
        super().__init__(status_code=status_code, detail=code)
        self.code = code


# --- factories, one per documented code ---------------------------------
def invalid_duration() -> APIError:
    return APIError(400, "invalid_duration")


def invalid_recipient() -> APIError:
    return APIError(400, "invalid_recipient")


def invalid_token() -> APIError:
    # Missing/malformed/unknown bearer token. (Distinct from agent_left_room.)
    return APIError(401, "invalid_token")


def room_full() -> APIError:
    return APIError(403, "room_full")


def room_not_found() -> APIError:
    return APIError(404, "room_not_found")


def message_not_found() -> APIError:
    # Unknown message, or one the caller didn't send (read receipts are sender-only).
    return APIError(404, "message_not_found")


def payload_too_large() -> APIError:
    return APIError(413, "payload_too_large")


def room_expired() -> APIError:
    return APIError(410, "room_expired")


def agent_left_room() -> APIError:
    return APIError(410, "agent_left_room")


def rate_limit_exceeded() -> APIError:
    return APIError(429, "rate_limit_exceeded")


def admin_unauthorized() -> APIError:
    # Missing/invalid admin token, or admin routes disabled (no token configured).
    return APIError(401, "admin_unauthorized")
