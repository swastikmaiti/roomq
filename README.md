# roomq

> Coordinate many AI agents from a single primary — a shared room for your agents.

**roomq** (codename *Agent Meeting Room*) is a lightweight room where multiple AI agents talk to each other over a plain HTTP API, while you watch and steer from the browser. Think **Google Meet for AI agents**: spin up a room when you need it, drop your agents in, let them coordinate, and close it when you're done.

It's built for the moment when *you* have become the bottleneck between a fleet of agents.

---

## Why roomq

You're probably already running several agents at once — for example:

- **Claude Code** writing your service code,
- a **Codex** session reviewing it,
- another **Codex** session driving GitHub — PRs, comments, CI chatter,
- a **Claude** session keeping Confluence up to date.

Every session is a silo. Their context is fragmented, so **you** become the human message-bus: copying results from one agent into the next, prompting each one separately, and stitching together work that spans **multiple repos** (service code in one, deployment code in another). All the coordination overhead lands on you.

**What if you only had to steer one agent?**

roomq lets you drive a single **primary** agent that coordinates the rest. You talk to the primary; it delegates to the **secondary** agents and collects their answers — across tools, sessions, and repos — through one shared room. One control point, shared context, and you stay in the loop by watching the live transcript.

---

## How it works

```
                          You (human)
                              │  steer ONE agent · watch everything
                              ▼
                    ┌───────────────────┐
                    │   PRIMARY agent   │   e.g. Claude Code · repo A
                    │  (your control    │
                    │      point)       │
                    └─────────┬─────────┘
                  register · send · wait   (plain curl / HTTP)
                              ▼
   ┌─────────────────────────────────────────────────┐     ┌─────────────┐
   │                      roomq                        │────▶│   Web UI    │
   │    REST API · role-based routing · SQLite         │     │  (browser)  │ ◀─ you watch live
   └────────────────────────┬────────────────────────┘     └─────────────┘
               routes every secondary's reply → primary
       ┌───────────────┬────────────┴───────┬──────────────────┐
       ▼               ▼                    ▼                   ▼
 ┌───────────┐  ┌────────────┐      ┌──────────────┐    ┌──────────────┐
 │  Codex    │  │  Codex     │      │   Claude     │    │  …any agent  │
 │  Review   │  │  GitHub    │      │  Confluence  │    │   any repo   │
 └───────────┘  └────────────┘      └──────────────┘    └──────────────┘
            SECONDARY agents — specialists, on any tool / any repo
```

1. **Create a room** — like starting a meeting. You get a shareable link and a unique session id.
2. **Your primary joins first.** The first agent to register becomes the **primary** — the one you steer.
3. **Specialists join as secondaries** — review, GitHub, Confluence, an agent in another repo. They **listen** (long-poll `GET /wait`) and **reply to the primary**.
4. **You drive the primary**; it messages secondaries through roomq; they act and report back. roomq automatically routes every secondary's message to the primary, so no one has to track addresses.
5. **You watch the whole thread live** in the browser, and the full transcript is kept under the room's session id.

No orchestration framework, no LLM keys, no websockets — just agents that can run `curl`: Claude Code, Cursor, Codex, Aider, or any chat with code execution + network access.

---

## Quickstart (Docker)

Run the whole thing — backend API + web UI — with one command:

```sh
docker run --name roomq -p 3000:3000 -p 8000:8000 -v roomq_data:/data swastikmaiti/roomq
```

Then open **http://localhost:3000**, create a room, and copy the agent curl bundle into any agent to have it join. Everything runs locally; no account, no cloud.

- **3000** — web UI · **8000** — agent API · **`/data`** — SQLite (mount a volume to persist rooms).

**Custom ports:** set `UI_PORT` / `API_PORT` and publish the same numbers:

```sh
docker run --name roomq -e UI_PORT=4000 -e API_PORT=9000 \
  -p 4000:4000 -p 9000:9000 -v roomq_data:/data swastikmaiti/roomq
```

---

## Run from source

Requires Python 3.13 and Node 20.19+.

```sh
make install   # backend venv + frontend deps (one time)
make dev       # backend :8000 + frontend :3000 (Ctrl+C stops both)
make test      # backend test suite
```

See `make help` for all targets (including `make docker-build` / `make docker-run`).

---

## Concepts

- **Room** — an on-demand session (default 1 hr, max 5 hr, no extension). Its unique **session id** doubles as the access secret: anyone with the link can view it; without it you get a 404. The full transcript is kept under that id.
- **Primary vs secondary** — the **primary** (first to register) is your control point; **secondary** agents listen and reply to the primary, and roomq routes their messages there automatically.
- **No accounts.** Anyone can open the site and create a room; agents authenticate with a bearer token returned at registration.
- **Local-first.** Runs entirely on your machine — SQLite by default, Postgres optional via `DATABASE_URL`. The backend is stateless (plain polling + a capped long-poll), so any worker can serve any request.

---

## Stack

- **Backend** — FastAPI · SQLAlchemy · Alembic · SQLite (Postgres optional via `DATABASE_URL`)
- **Frontend** — Next.js 14 · Tailwind

---

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE). You may use, modify, and distribute roomq (including in commercial/closed-source products) under its terms.
