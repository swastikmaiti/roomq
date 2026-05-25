"""Force a room to read as ended (testing/ops helper).

Sets ``expires_at`` to now, so agent routes start returning ``410 room_expired``
while snapshot/transcript keep serving the stored history. Nothing is deleted.

Usage:
    python -m scripts.force_expire <room_id>
"""

import sys

from app.database import SessionLocal
from app.models.room import Room
from app.util import utcnow


def main(room_id: str) -> int:
    db = SessionLocal()
    try:
        room = db.get(Room, room_id)
        if room is None:
            print(f"room not found: {room_id}")
            return 1
        room.expires_at = utcnow()
        db.commit()
        print(f"expired room {room_id}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python -m scripts.force_expire <room_id>")
        raise SystemExit(2)
    raise SystemExit(main(sys.argv[1]))
