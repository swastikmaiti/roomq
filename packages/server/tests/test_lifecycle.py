"""Leave (5b), agenda (5c), expiry, transcript (8), snapshot (11)."""

from tests.conftest import auth, create_room, force_expire, register


def test_leave_then_token_is_dead(client):
    room = create_room(client)
    b = register(client, room["room_id"], name="B")

    first = client.post(f"/rooms/{room['room_id']}/leave", headers=auth(b))
    assert first.json() == {"status": "left"}

    again = client.post(f"/rooms/{room['room_id']}/leave", headers=auth(b))
    assert again.status_code == 410
    assert again.json() == {"error": "agent_left_room"}

    poll = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b))
    assert poll.status_code == 410


def test_agenda_update_broadcasts_system_message(client):
    room = create_room(client, agenda="old")
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")

    resp = client.post(f"/rooms/{room['room_id']}/agenda", headers=auth(a), json={"agenda": "new goal"})
    assert resp.json() == {"status": "ok", "agenda": "new goal"}

    info = client.get(f"/rooms/{room['room_id']}/room_info", headers=auth(a)).json()
    assert info["agenda"] == "new goal"

    # B (not the updater) receives a system broadcast; A does not.
    b_inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b)).json()
    assert len(b_inbox["messages"]) == 1
    sys_msg = b_inbox["messages"][0]
    assert sys_msg["kind"] == "system"
    assert sys_msg["agent_id"] == "system"
    assert "new goal" in sys_msg["content"]

    a_inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(a)).json()
    assert a_inbox["messages"] == []


def test_expiry_blocks_agents_but_not_readers(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    # leave a message behind so readers have something to serve.
    client.post(
        f"/rooms/{room['room_id']}/messages",
        headers=auth(a),
        json={"messages": [{"to": b["agent_id"], "content": "before expiry", "in_reply_to": None}]},
    )
    force_expire(room["room_id"])

    # Every agent route returns 410 room_expired.
    assert client.get(f"/rooms/{room['room_id']}/messages", headers=auth(a)).json() == {"error": "room_expired"}
    assert client.get(f"/rooms/{room['room_id']}/room_info", headers=auth(a)).status_code == 410
    assert client.post(f"/rooms/{room['room_id']}/leave", headers=auth(a)).status_code == 410
    reg = client.post(f"/rooms/{room['room_id']}/register", json={"name": "late", "description": "x"})
    assert reg.json() == {"error": "room_expired"}

    # Readers keep working.
    assert client.get(f"/rooms/{room['room_id']}/snapshot").status_code == 200
    assert client.get(f"/rooms/{room['room_id']}/transcript").status_code == 200


def test_transcript_txt_and_json(client):
    room = create_room(client, agenda="topic")
    a = register(client, room["room_id"], name="Writer")
    b = register(client, room["room_id"], name="Reader")
    client.post(
        f"/rooms/{room['room_id']}/messages",
        headers=auth(a),
        json={"messages": [{"to": "all", "content": "broadcast hi", "in_reply_to": None}]},
    )

    txt = client.get(f"/rooms/{room['room_id']}/transcript", params={"format": "txt"})
    assert txt.status_code == 200
    assert "Agent Meeting Room — transcript" in txt.text
    assert "broadcast" in txt.text
    assert "Writer" in txt.text

    data = client.get(f"/rooms/{room['room_id']}/transcript", params={"format": "json"}).json()
    assert data["room_id"] == room["room_id"]
    assert {agent["name"] for agent in data["agents"]} == {"Writer", "Reader"}
    assert data["messages"][0]["from"] == a["agent_id"]
    assert data["messages"][0]["to"] == ["all"]


def test_rate_limit_returns_429(client, monkeypatch):
    from app.config import get_settings

    # Tighten the agenda limit so the test is fast and window-boundary safe.
    monkeypatch.setattr(get_settings(), "limit_room_agenda_per_min", 2)
    room = create_room(client)
    a = register(client, room["room_id"], name="A")

    for _ in range(2):
        ok = client.post(f"/rooms/{room['room_id']}/agenda", headers=auth(a), json={"agenda": "x"})
        assert ok.status_code == 200
    resp = client.post(f"/rooms/{room['room_id']}/agenda", headers=auth(a), json={"agenda": "y"})
    assert resp.status_code == 429
    assert resp.json() == {"error": "rate_limit_exceeded"}


def test_snapshot_exposes_room_link(client):
    room = create_room(client, agenda="kickoff")
    snap = client.get(f"/rooms/{room['room_id']}/snapshot").json()
    # room_link is what the viewer uses to build the copy-curl bundles.
    assert snap["room_link"].endswith(f"/rooms/{room['room_id']}")
    assert "joining_prompt" not in snap


def test_snapshot_cursor_and_read_by(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    client.post(
        f"/rooms/{room['room_id']}/messages",
        headers=auth(a),
        json={"messages": [{"to": b["agent_id"], "content": "m1", "in_reply_to": None}]},
    )

    snap = client.get(f"/rooms/{room['room_id']}/snapshot").json()
    assert snap["status"] == "live"
    assert len(snap["messages"]) == 1
    first_id = snap["messages"][0]["msg_id"]
    assert snap["messages"][0]["read_by"] == []  # not read yet

    client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b))  # B reads
    snap = client.get(f"/rooms/{room['room_id']}/snapshot").json()
    assert snap["messages"][0]["read_by"] == [b["agent_id"]]

    # since cursor returns only newer messages.
    client.post(
        f"/rooms/{room['room_id']}/messages",
        headers=auth(a),
        json={"messages": [{"to": b["agent_id"], "content": "m2", "in_reply_to": None}]},
    )
    newer = client.get(f"/rooms/{room['room_id']}/snapshot", params={"since": first_id}).json()
    assert [m["content"] for m in newer["messages"]] == ["m2"]
