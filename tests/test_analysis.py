"""The econometrics. Tested against closed-form cases, not against itself."""

import math

import pytest

from cost_to_orbit import analysis, load_dataset
from cost_to_orbit.models import PriceBasis


def test_ols_recovers_a_known_exponential_exactly():
    """Data generated as c_t = 100 * exp(-0.05 t) must return beta = -0.05."""
    points = [(year, 100 * math.exp(-0.05 * (year - 2000))) for year in range(2000, 2020)]
    fit = analysis.fit_log_linear_trend(points)

    assert fit.beta == pytest.approx(-0.05, abs=1e-9)
    assert fit.r_squared == pytest.approx(1.0, abs=1e-9)
    assert fit.annual_change == pytest.approx(math.exp(-0.05) - 1, abs=1e-9)
    assert fit.half_life_years == pytest.approx(math.log(0.5) / -0.05, rel=1e-9)


def test_half_life_is_none_when_cost_is_rising():
    points = [(2000, 100.0), (2001, 110.0), (2002, 121.0)]
    fit = analysis.fit_log_linear_trend(points)
    assert fit.beta > 0
    assert fit.half_life_years is None
    assert "rose" in fit.summary()


def test_trend_needs_enough_points():
    with pytest.raises(ValueError, match="at least 3 points"):
        analysis.fit_log_linear_trend([(2000, 1.0), (2001, 2.0)])


def test_trend_rejects_a_single_year():
    with pytest.raises(ValueError, match="slope is undefined"):
        analysis.fit_log_linear_trend([(2000, 1.0), (2000, 2.0), (2000, 3.0)])


def test_deflation_is_identity_in_the_base_year():
    ds = load_dataset()
    assert analysis.to_real(1000, ds.deflator.base_year, ds) == pytest.approx(1000)


def test_deflation_raises_past_dollars_toward_the_base_year():
    ds = load_dataset()
    assert analysis.to_real(1000, 1981, ds) > 1000


def test_frontier_deflates_from_price_year_not_anchor_year():
    """The 1981 Shuttle figure is quoted in 2008 dollars.

    Deflating it from 1981 would roughly double it and would put the real peak
    near $198k/kg instead of $84k/kg. This is the bug the price_year field exists
    to prevent, so it gets an explicit test.
    """
    ds = load_dataset()
    point = next(p for p in ds.frontier if p.year == 1981)
    assert point.price_year == 2008

    real = dict((y, c) for y, c, _ in analysis.real_frontier(ds))
    expected = point.cost_per_kg_leo * ds.deflator.factor(2008)
    wrong = point.cost_per_kg_leo * ds.deflator.factor(1981)

    assert real[1981] == pytest.approx(expected)
    assert real[1981] != pytest.approx(wrong)


def test_real_decline_exceeds_nominal_decline():
    ds = load_dataset()
    nominal = analysis.endpoint_decline(ds, real=False)["decline_factor"]
    real = analysis.endpoint_decline(ds, real=True)["decline_factor"]
    assert real > nominal


def test_endpoint_decline_flags_the_mixed_basis():
    """The headline ratio compares a program cost to a list price. Say so."""
    ds = load_dataset()
    d = analysis.endpoint_decline(ds)
    assert d["peak_price_basis"] != d["latest_price_basis"]
    assert "mixes bases" in d["caveat"]


def test_access_premium_holds_provider_and_year_fixed():
    ds = load_dataset()
    rideshare = ds.get("falcon-9-rideshare")
    dedicated = ds.get("falcon-heavy")
    assert rideshare.provider == dedicated.provider
    assert rideshare.price_year == dedicated.price_year

    a = analysis.access_premium(ds)
    assert a["premium_vs_frontier"] > 1
    assert a["rideshare_usd_per_kg"] == 7000


def test_rideshare_is_the_only_rideshare_row():
    ds = load_dataset()
    rows = ds.select(basis=PriceBasis.RIDESHARE)
    assert [v.id for v in rows] == ["falcon-9-rideshare"]


def test_since_filter_narrows_the_sample():
    ds = load_dataset()
    assert analysis.frontier_trend(ds, since=2010).n < analysis.frontier_trend(ds).n
