"""Public /stats aggregate counts."""

from tests.conftest import auth, create_room, force_expire, register


def test_stats_counts(client):
    assert client.get("/stats").json() == {
        "total_sessions": 0,
        "active_sessions": 0,
        "active_agents": 0,
    }

    r1 = create_room(client)
    r2 = create_room(client)
    register(client, r1["room_id"], name="A")
    register(client, r1["room_id"], name="B")

    s = client.get("/stats").json()
    assert s == {"total_sessions": 2, "active_sessions": 2, "active_agents": 2}

    # Expiring a room keeps the lifetime total, drops live counts (and its agents).
    force_expire(r1["room_id"])
    s = client.get("/stats").json()
    assert s == {"total_sessions": 2, "active_sessions": 1, "active_agents": 0}

    # An agent leaving a live room reduces active_agents but not session counts.
    c = register(client, r2["room_id"], name="C")
    assert client.get("/stats").json()["active_agents"] == 1
    client.post(f"/rooms/{r2['room_id']}/leave", headers=auth(c))
    assert client.get("/stats").json()["active_agents"] == 0
