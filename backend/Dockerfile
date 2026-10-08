# Build context: repo root (see docker-compose.yml).
# System packages are added by the phase that needs them (Pango for WeasyPrint in Phase 12).
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /srv
COPY pyproject.toml .
COPY backend/app/__init__.py backend/app/__init__.py
RUN pip install -e ".[dev]"

COPY . .
WORKDIR /srv/backend
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
