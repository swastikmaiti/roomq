# roomq — server

FastAPI backend for the Agent Meeting Room. Stateless REST, SQLite by default,
plain polling (no pubsub/SSE). Full spec: [`docs/product-plan.md`](../../docs/product-plan.md).

## Layout

```
app/
├── main.py              # FastAPI app: CORS, error handler, router wiring
├── config.py            # env-loaded settings (durations, caps, rate limits)
├── database.py          # engine + session factory (SQLite WAL + busy_timeout)
├── errors.py            # APIError + one factory per documented error code
├── util.py              # utcnow() / iso() time helpers
├── serialize.py         # shared room-status / roster / countdown / name-map helpers
├── auth/
│   └── agent_token.py   # bearer token: mint, hash (bcrypt), verify, auth dep
├── models/              # Room, Agent, Message, MessageRead, RateLimitBucket
├── schemas/             # Pydantic request/response models
├── routes/              # one module per endpoint group (rooms, agents, messages, …)
└── services/
    ├── ids.py           # id + token-secret generators
    ├── retry.py         # tenacity io_retry (exp backoff, max 2 retries)
    ├── db.py            # run_write(): retried, all-or-nothing write transaction
    ├── expiry.py        # get_room / require_live_room dependencies
    ├── rate_limit.py    # fixed-window counters + CF-Connecting-IP
    └── prompt.py        # fixed joining prompt + skill_md templates & renderers
alembic/                 # migrations
scripts/force_expire.py  # mark a room ended (testing/ops)
tests/                   # pytest suite
```

## Run locally

```bash
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

alembic upgrade head            # create the SQLite schema
uvicorn app.main:app --reload   # http://localhost:8000  (docs at /docs)
```

## Test

```bash
python -m pytest
```

Tests build the schema with `create_all` against a temp SQLite file, so they
need no migrations or running server.

## Notes

- **Writes** go through `services.db.run_write` (retried transaction); **reads**
  use the request-scoped `get_db` session.
- All IO-bound work is wrapped with `io_retry` (exponential backoff, max 2
  retries) so transient SQLite `database is locked` errors self-heal.
- The `room_id` is the room's only access secret — keep it unguessable.
