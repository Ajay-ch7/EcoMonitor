"""FastAPI application entry point."""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.db import get_engine
from app.schemas import Health, Region
from app.settings import Settings, get_settings

app = FastAPI(title="Land Emissions Monitor", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SettingsDep = Annotated[Settings, Depends(get_settings)]


def probe_database() -> Literal["ok", "unavailable"]:
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        return "unavailable"


@app.get("/health", response_model=Health)
def health(
    settings: SettingsDep,
    database: Annotated[Literal["ok", "unavailable"], Depends(probe_database)],
) -> Health:
    return Health(
        status="ok" if database == "ok" else "degraded",
        data_mode=settings.data_mode,
        region=settings.config.region.name,
        database=database,
    )


@app.get("/region", response_model=Region)
def region(settings: SettingsDep) -> Region:
    cfg = settings.config.region
    return Region(name=cfg.name, bbox=cfg.bbox)
