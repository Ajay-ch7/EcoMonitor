import pytest
from sqlalchemy import inspect, text

from app.db import Base, init_db

EXPECTED_TABLES = {
    "facilities",
    "detections",
    "events",
    "emission_estimates",
    "baseline_predictions",
    "anomalies",
    "exposures",
    "watchlists",
    "alert_deliveries",
    "layer_cache",
}


def test_models_define_expected_tables():
    from app import models  # noqa: F401

    assert set(Base.metadata.tables) == EXPECTED_TABLES


@pytest.mark.db
def test_init_db_creates_schema_on_postgis(db_engine):
    init_db(db_engine, reset=True)
    init_db(db_engine)  # second run is a no-op

    with db_engine.connect() as conn:
        assert conn.execute(text("SELECT postgis_version()")).scalar()
        assert set(inspect(conn).get_table_names()) >= EXPECTED_TABLES
