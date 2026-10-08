.PHONY: up down logs initdb resetdb seed test test-db lint fmt demo-record demo-replay

PY ?= python
COMPOSE ?= docker compose

# Start db (PostGIS), api, worker, web and mailhog. Creates .env on first run.
up:
	@test -f .env || cp .env.example .env
	$(COMPOSE) up -d --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f --tail=100

# Create PostGIS + all tables from app/models.py (idempotent). resetdb drops everything first.
initdb:
	$(COMPOSE) run --rm api python -m app.db

resetdb:
	$(COMPOSE) run --rm api python -m app.db --reset

seed:
	@echo "seed: implemented in Phase 3 (facility registry)"

# Local tests; DB tests skip without a database. test-db runs them in the api container.
test:
	DATA_MODE=fixture $(PY) -m pytest

test-db:
	$(COMPOSE) run --rm -e DATA_MODE=fixture -w /srv api python -m pytest

lint:
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

fmt:
	$(PY) -m ruff check --fix .
	$(PY) -m ruff format .

demo-record:
	@echo "demo-record: implemented in Phase 13"

demo-replay:
	@echo "demo-replay: implemented in Phase 13"
