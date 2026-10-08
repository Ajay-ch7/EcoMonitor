"""Pydantic schemas shared by detectors, the pipeline and the API.

Every detector returns ``list[Detection]``. Geometries are GeoJSON in WGS84 (EPSG:4326).
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

DetectorName = Literal["no2", "so2", "ch4", "flare", "thermal", "smoke"]
EventStatus = Literal["open", "rejected_crop_burning", "confirmed"]
Species = Literal["NO2", "NOx", "SO2"]
FacilityType = Literal["coal_power", "steel", "cement", "refinery", "smelter", "other"]


class GeoJSONGeometry(BaseModel):
    """Minimal GeoJSON geometry. Coordinates are [lon, lat]."""

    type: Literal["Point", "Polygon", "MultiPolygon", "LineString"]
    coordinates: Any


class Point(GeoJSONGeometry):
    type: Literal["Point"] = "Point"
    coordinates: tuple[float, float]

    @field_validator("coordinates")
    @classmethod
    def _wgs84(cls, v: tuple[float, float]) -> tuple[float, float]:
        lon, lat = v
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"not a WGS84 lon/lat: {v}")
        return v


class Polygon(GeoJSONGeometry):
    type: Literal["Polygon"] = "Polygon"
    coordinates: list[list[tuple[float, float]]]


class _Schema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class Facility(_Schema):
    id: int | None = None
    name: str
    operator: str | None = None
    type: FacilityType = "other"
    capacity_mw: float | None = None
    geom: Point
    footprint: Polygon | None = None
    sources: list[str] = Field(default_factory=list)
    source_ids: dict[str, Any] = Field(default_factory=dict)


class Detection(_Schema):
    id: int | None = None
    detector: DetectorName
    observed_at: datetime
    geom: Point
    footprint: Polygon | None = None
    value: float | None = None
    unit: str | None = None
    zscore: float | None = None
    class_label: str | None = None
    class_prob: float | None = Field(default=None, ge=0, le=1)
    qa: dict[str, Any] = Field(default_factory=dict)
    confidence: float = Field(default=0.0, ge=0, le=1)
    facility_id: int | None = None
    raw_ref: str | None = None


class Event(_Schema):
    id: int | None = None
    start_at: datetime
    end_at: datetime
    geom: GeoJSONGeometry
    facility_id: int | None = None
    detection_ids: list[int] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0, le=1)
    status: EventStatus = "open"
    summary: dict[str, Any] = Field(default_factory=dict)


class EmissionEstimate(_Schema):
    id: int | None = None
    facility_id: int
    species: Species
    period_start: date
    period_end: date
    rate_kg_s: float
    rate_low: float | None = None
    rate_high: float | None = None
    lifetime_h: float | None = None
    n_days: int | None = None
    method: str
    reference_value: float | None = None
    reference_source: str | None = None


class Exposure(_Schema):
    event_id: int
    plume_geom: Polygon
    population: float | None = None
    schools: int = 0
    hospitals: int = 0
    villages: int = 0
    site_list: list[dict[str, Any]] = Field(default_factory=list)


class Health(BaseModel):
    status: Literal["ok", "degraded"]
    data_mode: str
    region: str
    database: Literal["ok", "unavailable", "skipped"]


class Region(BaseModel):
    name: str
    bbox: tuple[float, float, float, float]
