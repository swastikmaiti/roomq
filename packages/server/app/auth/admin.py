"""Admin gate for the moderation endpoints.

A single shared secret (``settings.admin_token``) authorizes takedown routes.
If no token is configured the gate denies everything, so the admin surface is
off by default. The secret is accepted as ``Authorization: Bearer <token>`` or
the ``X-Admin-Token`` header, compared in constant time.
"""

import secrets as _secrets

from fastapi import Header

from app import errors
from app.config import get_settings


def require_admin(
    authorization: str | None = Header(default=None),
    x_admin_token: str | None = Header(default=None),
) -> None:
    configured = get_settings().admin_token
    if not configured:
        raise errors.admin_unauthorized()  # admin disabled

    provided = None
    if authorization and authorization.lower().startswith("bearer "):
        provided = authorization[len("bearer ") :].strip()
    elif x_admin_token:
        provided = x_admin_token.strip()

    if not provided or not _secrets.compare_digest(provided, configured):
        raise errors.admin_unauthorized()
