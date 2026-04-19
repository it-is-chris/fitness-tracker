import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from app.config import settings
from app.database import engine
from app.routers import auth, workouts, stats

# Import models so Alembic/SQLAlchemy registers them
import app.models  # noqa: F401


logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Alembic handles table creation via migrations — no create_all here
    yield
    await engine.dispose()


app = FastAPI(
    title="Fitness Tracker API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s %d %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


app.include_router(auth.router, prefix="/api")
app.include_router(workouts.router, prefix="/api")
app.include_router(stats.router, prefix="/api")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
