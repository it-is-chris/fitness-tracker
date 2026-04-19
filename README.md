# Fitness Tracker API

A REST API for tracking workouts, exercises, and personal records.

## Tech Stack

- **Framework**: FastAPI (async)
- **Database**: PostgreSQL (via asyncpg)
- **ORM**: SQLAlchemy 2.0 (async) + Alembic migrations
- **Auth**: JWT (PyJWT) + bcrypt password hashing
- **Testing**: pytest + httpx (async) against a real Postgres container (testcontainers)
- **Containerisation**: Docker + docker-compose
- **CI**: GitHub Actions (tests + image build on every PR)
- **Observability**: structured request logging, configurable log level, optional SQL echo

## Quick Start (Docker)

The fastest way to run the full stack (app + Postgres):

```bash
cp .env.example .env
# Edit .env — generate a SECRET_KEY:
# python -c "import secrets; print(secrets.token_hex(32))"

docker compose up --build
```

The API will be available at http://localhost:8000.
Interactive docs at http://localhost:8000/docs.

Migrations run automatically on container start.

## Local Development (without Docker)

### Prerequisites

- Python 3.12+
- PostgreSQL

### Install PostgreSQL (Ubuntu)

```bash
sudo apt install postgresql postgresql-contrib
sudo -u postgres createuser --interactive  # create your user
createdb fitness_tracker
```

### Install the project

```bash
# Create a virtual environment
uv venv --python 3.12    # or: python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt  # or: pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set your DATABASE_URL and generate a SECRET_KEY:
# python -c "import secrets; print(secrets.token_hex(32))"

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

## Configuration

Environment variables (set in `.env`):

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | — | Postgres connection string (async) |
| `SECRET_KEY` | — | JWT signing secret (required) |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | JWT expiry window |
| `LOG_LEVEL` | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`…) |
| `SQL_ECHO` | `false` | Log every SQL statement SQLAlchemy emits |

## Running Tests

Tests run against a real Postgres 16 container via [testcontainers](https://testcontainers.com/) — this avoids the SQLite/Postgres divergences (timezone-aware timestamps, `VARCHAR(n)` enforcement, collation-dependent `LOWER()`, float precision) that can let bugs pass tests and fail in production.

Each test runs inside a transaction that gets rolled back at the end, so tests are isolated without the cost of recreating tables every time.

```bash
docker info > /dev/null   # Docker must be running
pytest -v
```

The first run takes a few extra seconds while the Postgres image starts; subsequent runs reuse the cached image.

## Debugging

VS Code launch configurations are committed in `.vscode/launch.json`:
- **FastAPI** — runs the app under the debugger (uvicorn, no `--reload`).
- **Pytest: current file** — debugs the test file currently open.

Set breakpoints in the gutter and hit F5.

## API Endpoints

### Auth
- `POST /api/auth/register` — Create a new account
- `POST /api/auth/login` — Get a JWT token

### Workouts
- `POST /api/workouts` — Log a workout (with exercises and sets)
- `GET /api/workouts` — List your workouts
- `GET /api/workouts/{id}` — Get workout details
- `DELETE /api/workouts/{id}` — Delete a workout

### Stats
- `GET /api/stats/personal-records` — Get PRs per exercise
- `GET /api/stats/exercise-history?exercise_name=...` — Get history for an exercise

## Database Migrations

```bash
# Generate a new migration after changing models
alembic revision --autogenerate -m "describe your change"

# Apply migrations
alembic upgrade head

# Roll back one migration
alembic downgrade -1
```

## Project Roadmap

- [x] Phase 1: Core API (models, CRUD, auth, tests, Alembic)
- [x] Phase 2: Observability & debuggability (structured logging, request timing, configurable levels, VS Code debug configs)
- [x] Phase 3: Docker + CI (docker-compose stack, GitHub Actions)
- [ ] Phase 4: Next.js + TypeScript + Tailwind frontend (TanStack Query; PWA/offline layer added last)
- [ ] Phase 5: Redis (rate limiting on auth, caching on stats queries)
- [ ] Phase 6: Kubernetes deployment (managed cluster)
