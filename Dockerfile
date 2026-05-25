# Agent Meeting Room — all-in-one LOCAL image.
#
# Runs the FastAPI backend (:8000) and the Next.js UI (:3000) in a single
# container — the same pair `make dev` starts. This image is for running roomq
# locally and contains NO deploy tooling, infra, Cloudflare config, or secrets
# (the root .dockerignore whitelists only application source).
#
#   docker build -t swastikmaiti/roomq .
#   docker run -p 3000:3000 -p 8000:8000 -v roomq_data:/data swastikmaiti/roomq
#   → open http://localhost:3000
#
# Custom ports: set UI_PORT / API_PORT and publish the SAME numbers, e.g.
#   docker run -e UI_PORT=4000 -e API_PORT=9000 \
#     -p 4000:4000 -p 9000:9000 -v roomq_data:/data swastikmaiti/roomq
# The frontend's API origin is baked at build time as a placeholder and swapped
# to http://localhost:$API_PORT on startup, so the browser hits the right port.
#
# The browser calls the API directly on the published port, so this only works
# on localhost. It is not meant for hosting roomq on a public address.

FROM node:20-slim

# Backend runtime: Python in a venv (Debian's system pip is externally managed).
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-venv \
 && rm -rf /var/lib/apt/lists/*
ENV VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
RUN python3 -m venv "$VIRTUAL_ENV"

WORKDIR /app

# --- Backend dependencies (cached on requirements.txt) ---
COPY packages/server/requirements.txt server/requirements.txt
RUN pip install --no-cache-dir -r server/requirements.txt

# --- Frontend dependencies + build ---
COPY packages/ui/package.json packages/ui/package-lock.json ui/
RUN cd ui && npm ci
COPY packages/ui/ ui/
# NEXT_PUBLIC_API_URL is inlined at build time, so we bake a placeholder origin
# and rewrite it to the real host:port on startup (lets the user pick API_PORT).
# After building, drop devDeps (also removes the Cloudflare build tooling) so the
# runtime image keeps only what `next start` needs, then stash pristine copies of
# every built file containing the placeholder so each run can re-template cleanly.
ENV NEXT_PUBLIC_API_URL=http://roomq.api.origin.invalid
RUN cd ui \
 && npm run build \
 && npm prune --omit=dev \
 && grep -rl 'http://roomq.api.origin.invalid' .next 2>/dev/null \
      | while read -r f; do cp "$f" "$f.roomqorig"; done

# --- Backend source ---
COPY packages/server/ server/

# SQLite database lives at /data. Mount a volume there (-v roomq_data:/data) to
# persist rooms; without one the data stays in the container and is lost when the
# container is removed. No VOLUME directive on purpose: it would auto-create
# orphan anonymous volumes and make the data hint below always read "persisted".
# API_BASE_URL / UI_BASE_URL / CORS_ORIGINS are derived from the chosen ports by
# the entrypoint, so they're intentionally not pinned here.
RUN mkdir -p /data
ENV DATABASE_URL=sqlite:////data/roomq.db

# Migrate, then run backend + frontend together; exit if either one stops.
COPY <<'EOF' /usr/local/bin/entrypoint.sh
#!/bin/bash
set -e

# Ports are chosen at run time (defaults match the classic 3000/8000). Publish
# the SAME numbers with -p, e.g. -e API_PORT=9000 -p 9000:9000.
API_PORT="${API_PORT:-8000}"
UI_PORT="${UI_PORT:-3000}"
# Host-visible URLs the browser and agents use. Default to localhost on the
# chosen ports; override API_URL / UI_URL for a custom host or host:container map.
API_URL="${API_URL:-http://localhost:${API_PORT}}"
UI_URL="${UI_URL:-http://localhost:${UI_PORT}}"

# The backend builds room links + CORS from these.
export API_BASE_URL="$API_URL"
export UI_BASE_URL="$UI_URL"
export CORS_ORIGINS="$UI_URL"

# The frontend baked a placeholder API origin at build time. Restore the pristine
# copies first (so a fresh run with a different API_PORT re-templates correctly),
# then swap the placeholder for the real API_URL in the built files.
SENTINEL='http://roomq.api.origin.invalid'
find /app/ui/.next -name '*.roomqorig' 2>/dev/null | while read -r orig; do
  cp -f "$orig" "${orig%.roomqorig}"
done
grep -rl "$SENTINEL" /app/ui/.next 2>/dev/null | grep -v '\.roomqorig$' | while read -r f; do
  sed -i "s|${SENTINEL}|${API_URL}|g" "$f"
done

( cd /app/server && alembic upgrade head )

( cd /app/server && exec uvicorn app.main:app --host 0.0.0.0 --port "$API_PORT" --workers 2 ) &
api_pid=$!

( cd /app/ui && exec ./node_modules/.bin/next start -H 0.0.0.0 -p "$UI_PORT" ) &
ui_pid=$!

trap 'kill "$api_pid" "$ui_pid" 2>/dev/null' TERM INT

# Wait (up to ~30s) for both servers to accept connections, so the banner is the
# last thing printed instead of being buried in their startup logs.
wait_port() {
  for _ in $(seq 1 60); do
    (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && { exec 3>&-; return 0; }
    sleep 0.5
  done
}
wait_port "$API_PORT"
wait_port "$UI_PORT"

# OSC 8 hyperlink: clickable in terminals that support it, plain URL elsewhere.
hyperlink() { printf '\033]8;;%s\033\\%s\033]8;;\033\\' "$1" "$2"; }

# Tell the operator where their own room data lives and whether it will persist:
# /data is a mounted volume only if it shows up as its own mount point.
if grep -q ' /data ' /proc/mounts 2>/dev/null; then
  data_line='/data/roomq.db  (saved in your mounted volume)'
else
  data_line='/data/roomq.db  (ephemeral — add  -v roomq_data:/data  to keep it)'
fi

printf '\n'
printf '  ───────────────────────────────────────────────\n'
printf '   Agent Meeting Room is running.\n\n'
printf '   Open the UI:   '; hyperlink "$UI_URL" "$UI_URL"; printf '\n'
printf '   Agent API:     %s\n' "$API_URL"
printf '   Your data:     %s\n' "$data_line"
printf '   Stop:          press Ctrl+C\n'
printf '  ───────────────────────────────────────────────\n\n'

# If either process exits, tear the other down and stop the container.
wait -n "$api_pid" "$ui_pid"
kill "$api_pid" "$ui_pid" 2>/dev/null || true
EOF
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 3000 8000
CMD ["/usr/local/bin/entrypoint.sh"]
