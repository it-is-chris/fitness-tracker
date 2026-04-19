FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY alembic/ ./alembic/
COPY alembic.ini .

RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && gunicorn app.main:app -k uvicorn.workers.UvicornWorker -w 2 --bind 0.0.0.0:8000 --access-logfile -"]
