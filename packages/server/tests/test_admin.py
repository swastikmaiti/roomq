"""Admin moderation / takedown endpoints."""

from app.config import get_settings
from tests.conftest import auth, create_room, register

ADMIN = "test-admin-secret"


def _admin(token=ADMIN):
    return {"Authorization": f"Bearer {token}"}


def test_admin_disabled_without_token_config(client):
    # admin_token defaults to "" -> routes deny everything (admin off).
    room = create_room(client)
    assert client.delete(f"/rooms/{room['room_id']}", headers=_admin()).status_code == 401


def test_admin_delete_requires_valid_token(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "admin_token", ADMIN)
    room = create_room(client, agenda="x")
    assert client.delete(f"/rooms/{room['room_id']}").status_code == 401  # no token
    bad = client.delete(f"/rooms/{room['room_id']}", headers=_admin("nope"))
    assert bad.status_code == 401
    assert bad.json() == {"error": "admin_unauthorized"}


def test_admin_delete_room_cascades(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "admin_token", ADMIN)
    room = create_room(client, agenda="abusive room")
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    client.post(
        f"/rooms/{room['room_id']}/messages",
        headers=auth(a),
        json={"messages": [{"to": b["agent_id"], "content": "bad content", "in_reply_to": None}]},
    )
    assert len(client.get(f"/rooms/{room['room_id']}/snapshot").json()["messages"]) == 1

    resp = client.delete(f"/rooms/{room['room_id']}", headers=_admin())
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "deleted"
    assert resp.json()["messages_deleted"] == 1
    # Room and all its content are gone.
    assert client.get(f"/rooms/{room['room_id']}/snapshot").status_code == 404


def test_admin_delete_single_message(client, monkeypatch):
    monkeypatch.setattr(get_settings(), "admin_token", ADMIN)
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    register(client, room["room_id"], name="B")
    client.post(
        f"/rooms/{room['room_id']}/messages",
        headers=auth(a),
        json={"messages": [{"to": "all", "content": "oops sensitive", "in_reply_to": None}]},
    )
    mid = client.get(f"/rooms/{room['room_id']}/snapshot").json()["messages"][0]["msg_id"]

    resp = client.delete(f"/rooms/{room['room_id']}/messages/{mid}", headers=_admin())
    assert resp.status_code == 200, resp.text
    # Message gone, room still there.
    snap = client.get(f"/rooms/{room['room_id']}/snapshot").json()
    assert snap["messages"] == []
    assert snap["status"] == "live"

    # Deleting a nonexistent message -> 404.
    missing = client.delete(f"/rooms/{room['room_id']}/messages/msg-nope", headers=_admin())
    assert missing.status_code == 404
