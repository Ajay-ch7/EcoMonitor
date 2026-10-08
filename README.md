# Land Industrial Emissions Monitor

Detects, attributes and quantifies industrial NO₂/SO₂ emissions from satellite data, starting with the Singrauli coal belt (India).

> **Status:** early development. The foundation is in place: the API, the database schema, a background worker and a map UI. The detection, attribution and alerting modules are still being built (see [Roadmap](#roadmap)).

## Features

**Available now**

- **FastAPI backend** with `/health` (reports database status) and `/region` (monitored area from config).
- **PostGIS schema** for facilities, detections, events, emission estimates, baseline predictions, anomalies, population exposure, watchlists, alert deliveries and map-layer caching. All geometries are WGS84 (EPSG:4326).
- **Typed shared schemas** (Pydantic). Every detector returns a list of `Detection` objects, and tests check that the schemas match the database columns.
- **Background worker** (APScheduler) that runs scheduled jobs in the region's time zone.
- **Map dashboard** (Vite + React + TypeScript + MapLibre GL) that zooms to the configured region.
- **One config file**: region, thresholds, schedule and weights all live in `config/settings.yaml`.
- **Offline-first testing**: `DATA_MODE=fixture` means tests and CI never call external APIs.
- **Docker Compose stack** with PostGIS, API, worker, web and MailHog. CI runs on GitHub Actions.

## Tech stack

| Layer    | Tools                                                                |
| -------- | -------------------------------------------------------------------- |
| Backend  | Python 3.11, FastAPI, SQLAlchemy 2, GeoAlchemy2, pydantic-settings   |
| Database | PostgreSQL 16 + PostGIS 3.4                                          |
| Worker   | APScheduler                                                          |
| Frontend | Vite, React 19, TypeScript, MapLibre GL JS                           |
| Tooling  | pytest, ruff, Docker Compose, GitHub Actions                         |

## Getting started

### Prerequisites

- Docker with Docker Compose, plus `make`, **or**
- Python 3.11, Node.js 22 and a PostgreSQL/PostGIS server for a local setup without Docker

### Option A: Docker (recommended)

```bash
make up        # creates .env from .env.example if needed; starts db, api, worker, web, mailhog
make initdb    # enables PostGIS and creates all tables
```

| Service     | URL                          |
| ----------- | ---------------------------- |
| API health  | http://localhost:8000/health |
| API docs    | http://localhost:8000/docs   |
| Map         | http://localhost:5173        |
| MailHog     | http://localhost:8025        |

Other targets: `make down`, `make logs`, `make resetdb` (drops and recreates all tables).

### Option B: Local without Docker

```bash
cp .env.example .env                 # then set DATABASE_URL to your PostGIS server (host: localhost)

python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

cd backend
python -m app.db                     # create schema
uvicorn app.main:app --reload        # API on :8000
python -m app.jobs.scheduler         # worker (separate terminal)

cd ../web
npm install
npm run dev                          # map on :5173, proxies /api to :8000
```

## Configuration

| File                   | Purpose                                                                                      |
| ---------------------- | -------------------------------------------------------------------------------------------- |
| `.env`                 | Secrets and per-machine values: `DATABASE_URL`, `DATA_MODE` (`live` / `fixture` / `replay`), API keys. Copy from `.env.example`. **Never commit it.** |
| `config/settings.yaml` | Region bounding box, detector thresholds, schedule and weights                               |
| `config/regions/`      | Region boundary as GeoJSON                                                                    |
| `secrets/`             | Service-account key files (e.g. Earth Engine). Ignored by git.                               |

The credentials in `.env.example` (`emissions` / `emissions`) are for the local development database only. Use strong values anywhere else.

## Testing and linting

```bash
make test      # pytest locally; PostGIS tests are skipped if DATABASE_URL is unreachable
make test-db   # full suite inside the api container, against PostGIS
make lint      # ruff check + ruff format --check
make fmt       # auto-fix lint and formatting
```

CI ([.github/workflows/ci.yml](.github/workflows/ci.yml)) runs lint and the full test suite against a PostGIS service, and builds the web app.

## Project structure

```
.
├── backend/
│   ├── Dockerfile
│   └── app/
│       ├── main.py          # FastAPI app and routes
│       ├── settings.py      # .env + settings.yaml loading
│       ├── db.py            # engine, sessions, init_db (python -m app.db [--reset])
│       ├── models.py        # the only database schema definition
│       ├── schemas.py       # Pydantic schemas shared by detectors and API
│       ├── jobs/            # scheduler (worker entry point)
│       ├── clients/         # external data sources            (planned)
│       ├── registry/        # facility registry                (planned)
│       ├── detect/          # gas, flare, thermal, smoke       (planned)
│       ├── attribute/       # source attribution, emissions    (planned)
│       ├── temporal/        # baselines and anomaly alerts     (planned)
│       ├── impact/          # population / sensitive sites     (planned)
│       ├── alerts/          # geofenced email alerts           (planned)
│       ├── reports/         # PDF evidence reports             (planned)
│       ├── api/             # additional API routes            (planned)
│       └── demo/            # demo record / replay             (planned)
├── config/
│   ├── settings.yaml        # all thresholds and schedules
│   └── regions/             # region boundaries (GeoJSON)
├── data/                    # local caches and raw inputs (gitignored)
├── ml/                      # model training code              (planned)
├── models/                  # trained model weights (gitignored)
├── secrets/                 # key files (gitignored)
├── tests/                   # pytest suite and fixtures
├── web/                     # Vite + React + MapLibre dashboard
├── docker-compose.yml
├── Makefile
└── pyproject.toml           # package, pytest and ruff config
```

## Roadmap

1. ~~Repo skeleton, Docker, database~~ ✅
2. Data access layer (Earth Engine, NASA FIRMS, VIIRS Nightfire, OSM) with live and fixture modes
3. Facility registry (merge and de-duplicate public power-plant and industry datasets)
4. Gas detectors (NO₂, SO₂, CH₄, gas flaring) with confidence scoring
5. Attribution, multi-sensor fusion and emission-rate estimates
6. Thermal anomaly classifier
7. Stack smoke CNN
8. Per-facility baseline model and anomaly alerts
9. Population and sensitive-site exposure
10. Scheduled pipeline and API
11. Full map dashboard
12. Watchlists, geofenced email alerts and PDF reports
13. Integration, demo mode and hardening
