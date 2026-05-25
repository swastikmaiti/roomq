# Agent Meeting Room — local development.
#
#   make install   # one-time: backend venv + deps, frontend npm install
#   make dev       # start backend (:8000) + frontend (:3000); Ctrl+C stops both
#   make stop      # kill any stray dev servers
#   make test      # run the backend test suite
#
# Override ports/hosts if needed:  make dev UI_PORT=3001 API_PORT=8001

PYTHON   ?= python3.13
API_PORT ?= 8000
UI_PORT  ?= 3000
API_URL  ?= http://localhost:$(API_PORT)
UI_URL   ?= http://localhost:$(UI_PORT)
DB_URL   ?= sqlite:///./roomq.db

SERVER := packages/server
UI     := packages/ui

# All-in-one local image (published to Docker Hub).
IMAGE  ?= swastikmaiti/roomq

.DEFAULT_GOAL := help
.PHONY: help install install-server install-ui dev stop test clean docker-build docker-run

help: ## Show this help
	@echo "Agent Meeting Room — local dev"
	@echo ""
	@echo "  make install        one-time setup (backend venv + frontend deps)"
	@echo "  make dev            start backend + frontend (Ctrl+C stops both)"
	@echo "  make stop           stop any stray dev servers"
	@echo "  make test           run backend tests"
	@echo "  make clean          remove venv, node_modules, dev DB"
	@echo "  make docker-build   build the all-in-one image ($(IMAGE))"
	@echo "  make docker-run     run the all-in-one image (UI :$(UI_PORT), API :$(API_PORT))"

install: install-server install-ui ## Set up backend and frontend dependencies

install-server:
	cd $(SERVER) && $(PYTHON) -m venv .venv && .venv/bin/pip install -q --upgrade pip && .venv/bin/pip install -q -r requirements.txt
	@echo "✓ backend ready"

install-ui:
	cd $(UI) && npm install
	@echo "✓ frontend ready"

dev: ## Start backend + frontend; share the URL; Ctrl+C stops both
	@test -d $(SERVER)/.venv || { echo "Backend venv missing — run 'make install' first."; exit 1; }
	@test -d $(UI)/node_modules || { echo "Frontend deps missing — run 'make install' first."; exit 1; }
	@( cd $(SERVER) && DATABASE_URL="$(DB_URL)" .venv/bin/alembic upgrade head >/dev/null 2>&1 ) ; \
	trap 'kill 0' EXIT ; \
	( cd $(SERVER) && DATABASE_URL="$(DB_URL)" API_BASE_URL="$(API_URL)" UI_BASE_URL="$(UI_URL)" CORS_ORIGINS="$(UI_URL)" \
	    .venv/bin/uvicorn app.main:app --port $(API_PORT) --log-level warning ) & \
	printf '\n  ───────────────────────────────────────────────\n' ; \
	printf '   Agent Meeting Room is starting…\n\n' ; \
	printf '   Open in your browser:   %s\n' "$(UI_URL)" ; \
	printf '   Agent API host:         %s\n' "$(API_URL)" ; \
	printf '\n   Create a room in the UI, copy the agent curls,\n' ; \
	printf '   and paste them into a local agent to have it join.\n' ; \
	printf '   Press Ctrl+C to stop both servers.\n' ; \
	printf '  ───────────────────────────────────────────────\n\n' ; \
	( cd $(UI) && NEXT_PUBLIC_API_URL="$(API_URL)" npm run dev )

stop: ## Stop any stray dev servers
	-@pkill -f "uvicorn app.main:app" 2>/dev/null || true
	-@pkill -f "next dev" 2>/dev/null || true
	-@pkill -f "next-server" 2>/dev/null || true
	@echo "✓ stopped"

test: ## Run the backend test suite
	@test -d $(SERVER)/.venv || { echo "Backend venv missing — run 'make install' first."; exit 1; }
	cd $(SERVER) && .venv/bin/python -m pytest

clean: ## Remove venv, node_modules, and the dev database
	rm -rf $(SERVER)/.venv $(UI)/node_modules $(UI)/.next
	rm -f $(SERVER)/roomq.db $(SERVER)/roomq.db-wal $(SERVER)/roomq.db-shm
	@echo "✓ cleaned"

docker-build: ## Build the all-in-one local image
	docker build -t $(IMAGE) .

docker-run: ## Run the all-in-one image; open http://localhost:$(UI_PORT) (override UI_PORT/API_PORT)
	docker run --rm --name roomq \
	  -e UI_PORT=$(UI_PORT) -e API_PORT=$(API_PORT) \
	  -p $(UI_PORT):$(UI_PORT) -p $(API_PORT):$(API_PORT) \
	  -v roomq_data:/data $(IMAGE)
