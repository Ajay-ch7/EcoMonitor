import json

import pytest
from pydantic import ValidationError

from app.settings import RegionConfig, get_settings


def test_fixture_mode_in_tests():
    assert get_settings().data_mode == "fixture"


def test_settings_yaml_has_every_section():
    cfg = get_settings().config
    for section in ("data", "registry", "detect", "attribute", "temporal", "impact", "alerts", "schedule"):
        assert getattr(cfg, section), f"settings.yaml section '{section}' is empty"
    assert set(cfg.detect) >= {"no2", "so2", "ch4", "flaring", "thermal", "smoke", "confidence"}


def test_confidence_weights_sum_to_one():
    weights = get_settings().config.detect["confidence"]["weights"]
    assert sum(weights.values()) == pytest.approx(1.0)


def test_region_geojson_matches_bbox():
    settings = get_settings()
    region = settings.config.region
    with open(settings.resolve(region.geojson), encoding="utf-8") as f:
        ring = json.load(f)["features"][0]["geometry"]["coordinates"][0]
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    assert (min(lons), min(lats), max(lons), max(lats)) == region.bbox


def test_bad_bbox_rejected():
    with pytest.raises(ValidationError):
        RegionConfig(name="x", bbox=(83, 24, 82, 25), geojson="x.geojson")
