"""SQLAlchemy ORM models: the single definition of the database schema (see app.db.init_db).

Geometries are WGS84 (EPSG:4326).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from geoalchemy2 import Geometry
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base

FACILITY_TYPES = ("coal_power", "steel", "cement", "refinery", "smelter", "other")
DETECTORS = ("no2", "so2", "ch4", "flare", "thermal", "smoke")
EVENT_STATUSES = ("open", "rejected_crop_burning", "confirmed")
SPECIES = ("NO2", "NOx", "SO2")
DIRECTIONS = ("high", "low")


def _in(column: str, values: tuple[str, ...]) -> str:
    return f"{column} IN ({', '.join(repr(v) for v in values)})"


def point() -> Geometry:
    return Geometry("POINT", srid=4326, spatial_index=True)


def polygon() -> Geometry:
    return Geometry("POLYGON", srid=4326, spatial_index=True)


def any_geom() -> Geometry:
    return Geometry("GEOMETRY", srid=4326, spatial_index=True)


class Facility(Base):
    __tablename__ = "facilities"
    __table_args__ = (CheckConstraint(_in("type", FACILITY_TYPES), name="ck_facilities_type"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    operator: Mapped[str | None] = mapped_column(String(255))
    type: Mapped[str] = mapped_column(String(32), default="other")
    capacity_mw: Mapped[float | None] = mapped_column(Float)
    geom: Mapped[Any] = mapped_column(point())
    footprint: Mapped[Any | None] = mapped_column(polygon(), nullable=True)
    sources: Mapped[list[str]] = mapped_column(JSONB, default=list)
    source_ids: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class Detection(Base):
    __tablename__ = "detections"
    __table_args__ = (
        CheckConstraint(_in("detector", DETECTORS), name="ck_detections_detector"),
        CheckConstraint("confidence >= 0 AND confidence <= 1", name="ck_detections_confidence"),
        # NULLS NOT DISTINCT so re-runs stay idempotent for unattributed detections too (PostgreSQL 15+).
        UniqueConstraint(
            "detector",
            "facility_id",
            "observed_at",
            name="uq_detections_detector_facility_time",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    detector: Mapped[str] = mapped_column(String(16), index=True)
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    geom: Mapped[Any] = mapped_column(point())
    footprint: Mapped[Any | None] = mapped_column(polygon(), nullable=True)
    value: Mapped[float | None] = mapped_column(Float)
    unit: Mapped[str | None] = mapped_column(String(32))
    zscore: Mapped[float | None] = mapped_column(Float)
    class_label: Mapped[str | None] = mapped_column(String(32))
    class_prob: Mapped[float | None] = mapped_column(Float)
    qa: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    facility_id: Mapped[int | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"), index=True)
    raw_ref: Mapped[str | None] = mapped_column(Text)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (CheckConstraint(_in("status", EVENT_STATUSES), name="ck_events_status"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    end_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    geom: Mapped[Any] = mapped_column(any_geom())
    facility_id: Mapped[int | None] = mapped_column(ForeignKey("facilities.id", ondelete="SET NULL"), index=True)
    detection_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer), default=list)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(32), default="open")
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class EmissionEstimate(Base):
    __tablename__ = "emission_estimates"
    __table_args__ = (CheckConstraint(_in("species", SPECIES), name="ck_emission_estimates_species"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), index=True)
    species: Mapped[str] = mapped_column(String(8))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    rate_kg_s: Mapped[float] = mapped_column(Float)
    rate_low: Mapped[float | None] = mapped_column(Float)
    rate_high: Mapped[float | None] = mapped_column(Float)
    lifetime_h: Mapped[float | None] = mapped_column(Float)
    n_days: Mapped[int | None] = mapped_column(Integer)
    method: Mapped[str] = mapped_column(String(64))
    reference_value: Mapped[float | None] = mapped_column(Float)
    reference_source: Mapped[str | None] = mapped_column(String(255))


class BaselinePrediction(Base):
    __tablename__ = "baseline_predictions"

    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    observed: Mapped[float | None] = mapped_column(Float)
    expected: Mapped[float | None] = mapped_column(Float)
    residual: Mapped[float | None] = mapped_column(Float)
    residual_z: Mapped[float | None] = mapped_column(Float)


class Anomaly(Base):
    __tablename__ = "anomalies"
    __table_args__ = (CheckConstraint(_in("direction", DIRECTIONS), name="ck_anomalies_direction"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    facility_id: Mapped[int] = mapped_column(ForeignKey("facilities.id", ondelete="CASCADE"), index=True)
    date: Mapped[date] = mapped_column(Date, index=True)
    residual_z: Mapped[float] = mapped_column(Float)
    direction: Mapped[str] = mapped_column(String(8))
    matched_known_event: Mapped[str | None] = mapped_column(Text)


class Exposure(Base):
    __tablename__ = "exposures"

    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    plume_geom: Mapped[Any] = mapped_column(polygon())
    population: Mapped[float | None] = mapped_column(Float)
    schools: Mapped[int] = mapped_column(Integer, default=0)
    hospitals: Mapped[int] = mapped_column(Integer, default=0)
    villages: Mapped[int] = mapped_column(Integer, default=0)
    site_list: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)


class Watchlist(Base):
    """One geofenced area watched by one email address (#33)."""

    __tablename__ = "watchlists"
    __table_args__ = (
        CheckConstraint("min_confidence >= 0 AND min_confidence <= 1", name="ck_watchlists_min_confidence"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), index=True)
    name: Mapped[str | None] = mapped_column(String(255))
    geom: Mapped[Any] = mapped_column(polygon())
    species: Mapped[list[str]] = mapped_column(ARRAY(String(8)), default=list)  # empty = all species
    min_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AlertDelivery(Base):
    __tablename__ = "alert_deliveries"
    __table_args__ = (
        UniqueConstraint("watchlist_id", "event_id", name="uq_alert_deliveries_watchlist_event"),
        UniqueConstraint("watchlist_id", "anomaly_id", name="uq_alert_deliveries_watchlist_anomaly"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    watchlist_id: Mapped[int] = mapped_column(ForeignKey("watchlists.id", ondelete="CASCADE"), index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"))
    anomaly_id: Mapped[int | None] = mapped_column(ForeignKey("anomalies.id", ondelete="CASCADE"))
    email: Mapped[str] = mapped_column(String(320))
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(16), default="sent")
    error: Mapped[str | None] = mapped_column(Text)


class LayerCache(Base):
    __tablename__ = "layer_cache"

    layer: Mapped[str] = mapped_column(String(32), primary_key=True)
    date: Mapped[date] = mapped_column(Date, primary_key=True)
    ee_map_id: Mapped[str | None] = mapped_column(Text)
    tile_url: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
