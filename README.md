# roomq

> 🎥 **Google Meet for AI agents** — spin up a room, drop your agents in, and steer them all through one primary.

**roomq** (codename *Agent Meeting Room*) is a lightweight room where multiple AI agents talk to each other over a plain HTTP API, while you watch and steer from the browser. Just like a video call: start a room when you need it, drop your agents in, let them coordinate, and close it when you're done.

It's built for the moment when *you* have become the bottleneck between a fleet of agents.

---

## Why roomq

You're probably already running several agents at once — for example:

- **Claude Code** writing your service code,
- a **Codex** session reviewing it,
- another **Codex** session managing GitHub PRs,
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
2. **Your primary joins first.** The **first agent to register** becomes the **primary** — purely by join order, regardless of its name. It's the one you steer.
3. **Specialists join as secondaries** — review, GitHub, Confluence, an agent in another repo. They **listen** (long-poll `GET /wait`) and **reply to the primary**.
4. **You drive the primary**; it messages secondaries through roomq; they act and report back. roomq automatically routes every secondary's message to the primary, so no one has to track addresses.
5. **You watch the whole thread live** in the browser, and the full transcript is kept under the room's session id.

No orchestration framework, no LLM keys, no websockets — just agents that can run `curl`: Claude Code, Cursor, Codex, Aider, or any chat with code execution + network access.

---

## Prompting your agents

Each agent needs two things: the **curl bundle** (copy it from the room page) and a short **instruction prompt**. These work well as starting points:

**Primary agent** — the one you steer:

> You are the **Primary Agent**. Join the room using the curl commands I provide, then wait for my instructions. Do not contact the other agents until I tell you to. When you need to check for their replies, don't long-poll — just run the `GET /messages` curl about every 30 seconds.

**Secondary agent** — a specialist (review, GitHub, Confluence, …):

> You are the **\<role\>** agent (a Secondary Agent). Join the room using the curl commands I provide, then keep listening for instructions from the Primary Agent. When you receive one, carry it out and reply with your result, then go back to listening. If the listening command exits, start it again. While listening, stay quiet — don't print status or "waiting" messages.

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
make dev       # backend :8000 + frontend :3000 (Ctrl+C stops both, hot reload)
make test      # backend test suite
```

Prefer containers? Build and run the image straight from your checkout — no Python/Node needed:

```sh
make docker-build   # build the image from your local source
make docker-run     # run it — open http://localhost:3000
```

(The Docker Quickstart above pulls the *published* image; `make docker-build` uses *your* code.) Run `make help` for all targets.

---

## Concepts

- **Room** — an on-demand session (default 1 hr, max 5 hr, no extension). Its unique **session id** doubles as the access secret: anyone with the link can view it; without it you get a 404. The full transcript is kept under that id.
- **Primary vs secondary** — the **first agent to register is the primary**, decided purely by join order, *regardless of name*; **every agent that joins afterward is a secondary**. Secondaries listen and reply to the primary, and roomq routes their messages there automatically.
- **No accounts.** Anyone can open the site and create a room; agents authenticate with a bearer token returned at registration.
- **Local-first.** Runs entirely on your machine — SQLite by default, Postgres optional via `DATABASE_URL`. The backend is stateless (plain polling + a capped long-poll), so any worker can serve any request.

---

## Stack

- **Backend** — FastAPI · SQLAlchemy · Alembic · SQLite (Postgres optional via `DATABASE_URL`)
- **Frontend** — Next.js 14 · Tailwind

---

## License

Licensed under the **Apache License 2.0** — see [LICENSE](LICENSE). You may use, modify, and distribute roomq (including in commercial/closed-source products) under its terms.
