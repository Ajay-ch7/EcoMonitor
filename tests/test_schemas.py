from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app import models, schemas


def test_detection_roundtrip():
    d = schemas.Detection(
        detector="no2",
        observed_at=datetime(2026, 10, 1, 8, 0, tzinfo=UTC),
        geom=schemas.Point(coordinates=(82.6, 24.1)),
        value=1.2e-4,
        unit="mol/m2",
        zscore=3.1,
        confidence=0.8,
    )
    again = schemas.Detection.model_validate_json(d.model_dump_json())
    assert again == d
    assert again.geom.type == "Point"


@pytest.mark.parametrize(
    "bad",
    [
        {"detector": "co2"},
        {"confidence": 1.5},
        {"class_prob": -0.1},
        {"geom": {"type": "Point", "coordinates": (500, 24)}},
    ],
)
def test_detection_rejects_invalid(bad):
    base = {
        "detector": "so2",
        "observed_at": "2026-10-01T08:00:00Z",
        "geom": {"type": "Point", "coordinates": (82.6, 24.1)},
    }
    with pytest.raises(ValidationError):
        schemas.Detection.model_validate(base | bad)


def test_schema_literals_match_db_constraints():
    assert set(schemas.DetectorName.__args__) == set(models.DETECTORS)
    assert set(schemas.EventStatus.__args__) == set(models.EVENT_STATUSES)
    assert set(schemas.Species.__args__) == set(models.SPECIES)
    assert set(schemas.FacilityType.__args__) == set(models.FACILITY_TYPES)


@pytest.mark.parametrize(
    ("schema", "table"),
    [
        (schemas.Facility, models.Facility),
        (schemas.Detection, models.Detection),
        (schemas.Event, models.Event),
        (schemas.EmissionEstimate, models.EmissionEstimate),
        (schemas.Exposure, models.Exposure),
    ],
)
def test_schema_fields_match_table_columns(schema, table):
    assert set(schema.model_fields) == set(table.__table__.columns.keys())
