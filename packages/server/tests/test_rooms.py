"""Endpoint 1 — room creation and the duration guard."""

from tests.conftest import create_room


def test_create_with_default_duration(client):
    room = create_room(client)
    assert room["room_id"]
    assert room["viewer_link"] == f"http://ui.test/rooms/{room['room_id']}"
    assert room["room_link"] == f"http://api.test/rooms/{room['room_id']}"
    assert room["agenda"] is None
    assert "joining_prompt" not in room


def test_create_with_custom_duration_and_agenda(client):
    room = create_room(client, active_for_minutes=120, agenda="Plan the launch")
    assert room["agenda"] == "Plan the launch"


def test_duration_below_min_is_rejected(client):
    resp = client.post("/rooms", json={"active_for_minutes": 30})
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_duration"}


def test_duration_above_max_is_rejected(client):
    resp = client.post("/rooms", json={"active_for_minutes": 301})
    assert resp.status_code == 400
    assert resp.json() == {"error": "invalid_duration"}


def test_agenda_is_capped_at_200_chars(client):
    room = create_room(client, agenda="x" * 500)
    assert len(room["agenda"]) == 200


def test_unknown_room_is_404(client):
    resp = client.get("/rooms/nope/snapshot")
    assert resp.status_code == 404
    assert resp.json() == {"error": "room_not_found"}
