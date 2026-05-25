"""Endpoints 4 (poll), 5 (send), 10 (read receipts)."""

from tests.conftest import auth, create_room, register


def _send(client, room_id, sender, messages):
    return client.post(
        f"/rooms/{room_id}/messages", headers=auth(sender), json={"messages": messages}
    )


def test_direct_send_and_poll_marks_read(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")

    resp = _send(client, room["room_id"], a, [{"to": b["agent_id"], "content": "hi B", "in_reply_to": None}])
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b)).json()
    assert [m["content"] for m in inbox["messages"]] == ["hi B"]
    assert inbox["messages"][0]["agent_id"] == a["agent_id"]
    assert inbox["messages"][0]["agent_name"] == "A"

    # Second poll: already read.
    again = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b)).json()
    assert again["messages"] == []
    assert again["status"] == "no_new_messages"


def test_broadcast_reaches_others_but_not_sender(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    c = register(client, room["room_id"], name="C")

    _send(client, room["room_id"], a, [{"to": "all", "content": "hello room", "in_reply_to": None}])

    for agent in (b, c):
        inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(agent)).json()
        assert len(inbox["messages"]) == 1
        assert inbox["messages"][0]["broadcast"] is True
    sender_inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(a)).json()
    assert sender_inbox["messages"] == []


def test_self_address_is_dropped(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    _send(client, room["room_id"], a, [{"to": a["agent_id"], "content": "to myself", "in_reply_to": None}])
    inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(a)).json()
    assert inbox["messages"] == []


def test_batch_over_cap_rejected(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    batch = [{"to": b["agent_id"], "content": "x", "in_reply_to": None} for _ in range(11)]
    resp = _send(client, room["room_id"], a, batch)
    assert resp.status_code == 413
    assert resp.json() == {"error": "payload_too_large"}


def test_oversize_content_rejected(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    resp = _send(client, room["room_id"], a, [{"to": b["agent_id"], "content": "x" * 33000, "in_reply_to": None}])
    assert resp.status_code == 413


def test_addressing_system_is_invalid(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    resp = _send(client, room["room_id"], a, [{"to": "system", "content": "hi", "in_reply_to": None}])
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_recipient"}


def test_send_to_left_agent_reported(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    client.post(f"/rooms/{room['room_id']}/leave", headers=auth(b))

    resp = _send(client, room["room_id"], a, [{"to": b["agent_id"], "content": "still there?", "in_reply_to": None}])
    body = resp.json()
    assert body["status"] == "ok"
    assert body["left_agents"] == [{"agent_id": b["agent_id"], "name": "B"}]


def test_read_receipts_sender_only(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")

    _send(client, room["room_id"], a, [{"to": b["agent_id"], "content": "ping", "in_reply_to": None}])
    # find the message id via snapshot
    snap = client.get(f"/rooms/{room['room_id']}/snapshot").json()
    mid = snap["messages"][0]["msg_id"]

    # Before B reads: read_at is null.
    reads = client.get(f"/rooms/{room['room_id']}/messages/{mid}/reads", headers=auth(a)).json()
    assert reads["reads"][0]["read_at"] is None

    client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b))  # B reads
    reads = client.get(f"/rooms/{room['room_id']}/messages/{mid}/reads", headers=auth(a)).json()
    assert reads["reads"][0]["agent_id"] == b["agent_id"]
    assert reads["reads"][0]["read_at"] is not None

    # Non-sender cannot see receipts; unknown message id 404s.
    assert client.get(f"/rooms/{room['room_id']}/messages/{mid}/reads", headers=auth(b)).status_code == 404
    assert client.get(f"/rooms/{room['room_id']}/messages/msg-nope/reads", headers=auth(a)).status_code == 404


def test_optional_fields_omitted_when_not_relevant(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")

    # A direct send with no left recipients omits left_agents entirely.
    send = _send(client, room["room_id"], a, [{"to": b["agent_id"], "content": "hi", "in_reply_to": None}]).json()
    assert send == {"status": "ok"}

    inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b)).json()
    msg = inbox["messages"][0]
    assert "broadcast" not in msg  # only present when true
    assert "kind" not in msg  # only present for system
    assert "in_reply_to" in msg and msg["in_reply_to"] is None  # always present
    assert "status" not in inbox  # non-empty inbox has no status

    # Empty inbox uses the no_new_messages shape.
    empty = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b)).json()
    assert empty == {"messages": [], "status": "no_new_messages"}


def test_secondary_routes_to_primary_without_to(client):
    room = create_room(client)
    primary = register(client, room["room_id"], name="Primary")  # first => primary
    secondary = register(client, room["room_id"], name="Secondary")
    other = register(client, room["room_id"], name="Other")

    # Secondary sends with NO `to` — server routes it to the primary.
    resp = _send(client, room["room_id"], secondary, [{"content": "for primary", "in_reply_to": None}])
    assert resp.json() == {"status": "ok"}

    p_inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(primary)).json()
    assert [m["content"] for m in p_inbox["messages"]] == ["for primary"]
    # The other secondary gets nothing.
    o_inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(other)).json()
    assert o_inbox["messages"] == []


def test_secondary_to_is_ignored_and_forced_to_primary(client):
    room = create_room(client)
    primary = register(client, room["room_id"], name="Primary")
    secondary = register(client, room["room_id"], name="Secondary")
    other = register(client, room["room_id"], name="Other")

    # Secondary tries to address the other secondary; server overrides to primary.
    _send(client, room["room_id"], secondary, [{"to": other["agent_id"], "content": "hi", "in_reply_to": None}])

    assert [m["content"] for m in client.get(
        f"/rooms/{room['room_id']}/messages", headers=auth(primary)
    ).json()["messages"]] == ["hi"]
    assert client.get(f"/rooms/{room['room_id']}/messages", headers=auth(other)).json()["messages"] == []


def test_primary_must_address_someone(client):
    room = create_room(client)
    primary = register(client, room["room_id"], name="Primary")
    register(client, room["room_id"], name="Secondary")

    resp = _send(client, room["room_id"], primary, [{"content": "to nobody", "in_reply_to": None}])
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_recipient"}


def test_wait_returns_pending_message_and_marks_read(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    _send(client, room["room_id"], a, [{"to": b["agent_id"], "content": "hi B", "in_reply_to": None}])

    # A message is already waiting, so /wait returns it on the first check.
    inbox = client.get(f"/rooms/{room['room_id']}/wait", headers=auth(b)).json()
    assert [m["content"] for m in inbox["messages"]] == ["hi B"]
    assert "status" not in inbox  # non-empty inbox omits status

    # It was marked read — a follow-up /messages is empty.
    again = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(b)).json()
    assert again == {"messages": [], "status": "no_new_messages"}


def test_wait_times_out_to_no_new_messages(client, monkeypatch):
    from app.config import get_settings

    # Zero hold so the loop returns empty immediately instead of sleeping.
    monkeypatch.setattr(get_settings(), "wait_max_seconds", 0)
    room = create_room(client)
    b = register(client, room["room_id"], name="B")

    resp = client.get(f"/rooms/{room['room_id']}/wait", headers=auth(b))
    assert resp.status_code == 200
    assert resp.json() == {"messages": [], "status": "no_new_messages"}


def test_wait_requires_valid_token(client):
    room = create_room(client)
    register(client, room["room_id"], name="A")
    assert client.get(f"/rooms/{room['room_id']}/wait").status_code == 401
    bad = client.get(
        f"/rooms/{room['room_id']}/wait",
        headers={"Authorization": "Bearer agt-x.wrong"},
    )
    assert bad.status_code == 401
    assert bad.json() == {"error": "invalid_token"}


def test_in_reply_to_is_preserved(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="A")
    b = register(client, room["room_id"], name="B")
    _send(client, room["room_id"], a, [{"to": b["agent_id"], "content": "q", "in_reply_to": None}])
    snap = client.get(f"/rooms/{room['room_id']}/snapshot").json()
    first = snap["messages"][0]["msg_id"]
    _send(client, room["room_id"], b, [{"to": a["agent_id"], "content": "answer", "in_reply_to": first}])
    inbox = client.get(f"/rooms/{room['room_id']}/messages", headers=auth(a)).json()
    assert inbox["messages"][0]["in_reply_to"] == first
