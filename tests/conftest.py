from __future__ import annotations

import os

# Tests never touch live services.
os.environ["DATA_MODE"] = "fixture"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db import get_engine  # noqa: E402
from app.main import app, probe_database  # noqa: E402
from app.settings import get_settings  # noqa: E402

get_settings.cache_clear()


@pytest.fixture
def client() -> TestClient:
    app.dependency_overrides[probe_database] = lambda: "ok"
    yield TestClient(app)
    app.dependency_overrides.clear()


def _database_available() -> bool:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.fixture(scope="session")
def db_engine():
    if not _database_available():
        pytest.skip(f"no database at {get_settings().database_url}")
    return get_engine()
