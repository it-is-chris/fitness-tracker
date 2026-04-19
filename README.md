# Fitness Tracker API

A REST API for tracking workouts, exercises, and personal records.

## Tech Stack

- **Framework**: FastAPI
- **Database**: PostgreSQL (via asyncpg)
- **ORM**: SQLAlchemy (async) + Alembic migrations
- **Auth**: JWT (python-jose + bcrypt)
- **Testing**: pytest + httpx (async)

## Setup

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
# Clone and enter the project
cd fitness-tracker

# Create a virtual environment
uv venv --python 3.12    # or: python3.12 -m venv venv
source .venv/bin/activate  # or: source venv/bin/activate

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

The API will be available at http://localhost:8000.
Interactive docs at http://localhost:8000/docs.

### Run tests

Tests use an in-memory SQLite database — no PostgreSQL needed.

```bash
pytest -v
```

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
- [ ] Phase 2: Redis caching + background tasks
- [ ] Phase 3: Docker + CI (GitHub Actions)
- [ ] Phase 4: React + TypeScript + Tailwind frontend
- [ ] Phase 5: Kubernetes deployment
