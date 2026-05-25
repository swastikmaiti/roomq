"""Endpoints 2 (register) and 3 (room_info)."""

from tests.conftest import auth, create_room, register


def test_register_returns_identity(client):
    room = create_room(client, agenda="ship it")
    agent = register(client, room["room_id"], name="Researcher")

    assert agent["status"] == "ok"
    assert agent["agent_id"].startswith("agt-")
    assert agent["name"] == "Researcher"
    # Token is {agent_id}.{secret}.
    assert agent["token"].startswith(agent["agent_id"] + ".")
    # The slim join response carries nothing else — no playbook/roster/setup.
    assert set(agent) == {"status", "agent_id", "name", "token"}


def test_name_collision_is_suffixed(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="Twin")
    b = register(client, room["room_id"], name="Twin")
    assert a["name"] == "Twin"
    assert b["name"] == "Twin-2"


def test_room_full_at_cap(client):
    room = create_room(client)
    for i in range(20):
        register(client, room["room_id"], name=f"A{i}")
    resp = client.post(
        f"/rooms/{room['room_id']}/register",
        json={"name": "overflow", "description": "late"},
    )
    assert resp.status_code == 403
    assert resp.json() == {"error": "room_full"}


def test_room_info_requires_valid_token(client):
    room = create_room(client)
    register(client, room["room_id"], name="A")

    assert client.get(f"/rooms/{room['room_id']}/room_info").status_code == 401
    bad = client.get(
        f"/rooms/{room['room_id']}/room_info",
        headers={"Authorization": "Bearer agt-x.wrong"},
    )
    assert bad.status_code == 401
    assert bad.json() == {"error": "invalid_token"}


def test_room_info_reports_status_and_roster(client):
    room = create_room(client, agenda="goal")
    a = register(client, room["room_id"], name="A")
    register(client, room["room_id"], name="B")

    info = client.get(f"/rooms/{room['room_id']}/room_info", headers=auth(a)).json()
    assert info["status"] == "live"
    assert info["agenda"] == "goal"
    assert info["seconds_remaining"] > 0
    assert {e["name"] for e in info["agents"]} == {"A", "B"}


def test_roster_includes_agent_details(client):
    room = create_room(client)
    a = register(client, room["room_id"], name="Researcher", description="gathers sources")

    # room_info roster carries the self-advertised description (so agents/humans
    # can tell who is who). Skills/capabilities are no longer collected.
    entry = client.get(f"/rooms/{room['room_id']}/room_info", headers=auth(a)).json()["agents"][0]
    assert entry["description"] == "gathers sources"
    assert entry["skills"] is None
    assert entry["capabilities"] is None

    # snapshot (public, powers the viewer) carries the description too.
    snap_entry = client.get(f"/rooms/{room['room_id']}/snapshot").json()["agents"][0]
    assert snap_entry["description"] == "gathers sources"
