"""Database engine, sessions and schema creation.

The schema is defined once, in app/models.py. `python -m app.db` creates PostGIS and any
missing tables; `python -m app.db --reset` drops and recreates everything (all data is
re-creatable from fixtures or live sources).
"""

from __future__ import annotations

import argparse
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.settings import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine() -> Engine:
    # Short connect timeout so /health and test probes fail fast when the DB is down.
    return create_engine(get_settings().database_url, pool_pre_ping=True, connect_args={"connect_timeout": 3})


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_session() -> Iterator[Session]:
    """FastAPI dependency yielding a session."""
    with get_sessionmaker()() as session:
        yield session


def init_db(engine: Engine | None = None, reset: bool = False) -> None:
    """Enable PostGIS and create all tables from app.models. Safe to run repeatedly."""
    from app import models  # noqa: F401  (registers tables on Base.metadata)

    engine = engine or get_engine()
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    if reset:
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create (or reset) the database schema.")
    parser.add_argument("--reset", action="store_true", help="drop all tables first")
    args = parser.parse_args()
    init_db(reset=args.reset)
    print("database ready" + (" (reset)" if args.reset else ""))
