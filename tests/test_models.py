"""The schema's job is to make a wrong number impossible to commit."""

import math

import pytest
from pydantic import ValidationError

from cost_to_orbit.models import Confidence, Deflator, PriceBasis, Status, Vehicle

BASE = {
    "id": "test-vehicle",
    "name": "Test Vehicle",
    "provider": "Test",
    "country": "USA",
    "status": Status.ACTIVE,
    "reusable": "expendable",
    "confidence": Confidence.HIGH,
    "source": "test",
}


def make(**overrides) -> Vehicle:
    return Vehicle(**{**BASE, **overrides})


def test_cost_per_kg_must_equal_price_over_payload():
    with pytest.raises(ValidationError, match="price/payload gives"):
        make(
            payload_leo_kg=1000,
            price_usd=10_000_000,
            price_year=2026,
            price_basis=PriceBasis.DEDICATED_LIST,
            cost_per_kg_leo=5_000,  # truth is 10,000
        )


def test_rounding_within_tolerance_is_accepted():
    v = make(
        payload_leo_kg=63800,
        price_usd=97_000_000,
        price_year=2026,
        price_basis=PriceBasis.DEDICATED_LIST,
        cost_per_kg_leo=1520,  # 1520.37 rounded
    )
    assert v.cost_per_kg_leo == 1520


def test_price_without_basis_is_rejected():
    with pytest.raises(ValidationError, match="no price_basis"):
        make(payload_leo_kg=1000, price_usd=1_000_000, price_year=2026, cost_per_kg_leo=1000)


def test_cost_without_price_is_rejected():
    """Stops a hand-typed $/kg with nothing behind it."""
    with pytest.raises(ValidationError, match="no price and payload"):
        make(cost_per_kg_leo=1234)


def test_point_estimate_must_sit_inside_its_range():
    with pytest.raises(ValidationError, match="outside its stated range"):
        make(
            payload_leo_kg=1000,
            price_usd=50_000_000,
            price_usd_low=10_000_000,
            price_usd_high=20_000_000,
            price_year=2026,
            price_basis=PriceBasis.ESTIMATE,
            cost_per_kg_leo=50_000,
        )


def test_half_a_range_is_rejected():
    with pytest.raises(ValidationError, match="both low and high"):
        make(price_usd_low=1_000_000)


def test_unpriced_vehicle_is_valid():
    """Starship has no price. That has to be representable, not an error."""
    v = make(id="starship", payload_leo_kg=100_000, confidence=Confidence.LOW)
    assert v.cost_per_kg_leo is None


def test_deflator_factor_and_base_year():
    d = Deflator(
        series="test",
        source="test",
        base_year=2026,
        values={2000: 100.0, 2026: 200.0},
    )
    assert d.factor(2026) == 1.0
    assert math.isclose(d.factor(2000), 2.0)
    with pytest.raises(KeyError):
        d.factor(1900)


def test_deflator_requires_its_base_year():
    with pytest.raises(ValidationError, match="missing from the index"):
        Deflator(series="t", source="t", base_year=2026, values={2000: 100.0})
