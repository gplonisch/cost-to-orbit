"""Checks on the shipped data, not on hypothetical data."""

from cost_to_orbit import load_dataset
from cost_to_orbit.models import Confidence, PriceBasis, Status


def test_dataset_loads_and_validates():
    ds = load_dataset()
    assert len(ds.vehicles) >= 15
    assert len(ds.frontier) >= 5


def test_every_priced_row_can_be_deflated():
    """A price year with no CPI value silently breaks every real-terms figure."""
    ds = load_dataset()
    for v in ds.vehicles:
        if v.price_year is not None:
            assert v.price_year in ds.deflator.values, f"{v.id}: no CPI for {v.price_year}"


def test_vehicle_ids_are_unique():
    ds = load_dataset()
    ids = [v.id for v in ds.vehicles]
    assert len(ids) == len(set(ids))


def test_starship_carries_no_price():
    """The whole point of the dataset is that aspirational targets stay out."""
    ds = load_dataset()
    starship = ds.get("starship")
    assert starship.price_usd is None
    assert starship.cost_per_kg_leo is None
    assert starship in ds.unpriced()


def test_cheapest_dedicated_operational_is_falcon_heavy():
    ds = load_dataset()
    cheapest = ds.cheapest(basis=PriceBasis.DEDICATED_LIST, operational_only=True)
    assert cheapest.id == "falcon-heavy"


def test_filtering_by_basis_excludes_other_bases():
    ds = load_dataset()
    rows = ds.select(basis=PriceBasis.PROGRAM_COST)
    assert {v.id for v in rows} == {"space-shuttle", "saturn-v"}


def test_projected_vehicles_are_not_operational():
    ds = load_dataset()
    assert ds.get("neutron").status is Status.PROJECTED
    assert not ds.get("neutron").is_operational
    assert ds.get("neutron") not in ds.select(operational_only=True)


def test_min_confidence_filter_is_a_floor():
    ds = load_dataset()
    rows = ds.select(min_confidence=Confidence.HIGH)
    assert rows
    assert all(v.confidence is Confidence.HIGH for v in rows)


def test_every_row_has_a_source():
    ds = load_dataset()
    for v in ds.vehicles:
        assert v.source.strip(), f"{v.id} has no source"
