"""Test fixtures.

A file-based SQLite DB (not ``:memory:``) is used so the multiple sessions a
single request opens — the request-scoped read session plus ``run_write``'s
write session — all see the same data. The schema is recreated per test for
isolation.
"""

import os
import pathlib
import tempfile

# Must be set before importing anything that builds the engine / settings.
_TEST_DB = pathlib.Path(tempfile.gettempdir()) / "roomq_test.db"
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB}"
os.environ["API_BASE_URL"] = "http://api.test"
os.environ["UI_BASE_URL"] = "http://ui.test"

import app.models  # noqa: E402,F401  (registers tables on Base.metadata)
import pytest  # noqa: E402
from app.database import Base, SessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.room import Room  # noqa: E402
from app.util import utcnow  # noqa: E402
from datetime import timedelta  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture
def client():
    return TestClient(app)


# --- helpers -------------------------------------------------------------
def create_room(client, **body):
    resp = client.post("/rooms", json=body)
    assert resp.status_code == 200, resp.text
    return resp.json()


def register(client, room_id, name="Agent", description="does things", **extra):
    resp = client.post(
        f"/rooms/{room_id}/register",
        json={"name": name, "description": description, **extra},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def auth(agent):
    return {"Authorization": f"Bearer {agent['token']}"}


def force_expire(room_id):
    """Push a room's expires_at into the past (mirrors scripts/force_expire.py)."""
    db = SessionLocal()
    try:
        room = db.get(Room, room_id)
        room.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()
    finally:
        db.close()
