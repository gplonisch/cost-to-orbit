"""The economics: deflation, the decline rate, and the access premium.

Three things here, in order of how much they change the story.

1. Deflation. Launch prices are quoted in the dollars of whatever year they
   were quoted in. Comparing a 1981 figure to a 2026 figure without deflating
   attributes 45 years of general inflation to the rocket industry.

2. The decline rate. The standard claim is that launch cost "fell 20x." That
   is a statement about two endpoints. Fitting a trend gives the shape, and
   the shape has a break in it that the endpoint comparison hides.

3. The access premium. The frontier price is the price of buying an entire
   Falcon Heavy at its maximum expendable payload. The price of putting one
   small satellite in orbit is several times higher. For most customers the
   second number is the real one.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from cost_to_orbit.dataset import Dataset, load_dataset
from cost_to_orbit.models import PriceBasis


# ---------------------------------------------------------------------------
# 1. Nominal to real
# ---------------------------------------------------------------------------
def to_real(
    nominal_usd: float,
    from_year: int,
    dataset: Dataset | None = None,
) -> float:
    """Convert nominal dollars of `from_year` into base-year dollars.

    real = nominal * (CPI_base / CPI_from)

    The base year is set in data/deflator.json. CPI-U is the right index here
    because these are prices paid, not output deflated; a GDP deflator or a
    capital-goods PPI would be defensible alternatives and would shift the
    pre-2000 figures noticeably.
    """
    ds = dataset or load_dataset()
    return nominal_usd * ds.deflator.factor(from_year)


def real_frontier(dataset: Dataset | None = None) -> list[tuple[int, float, bool]]:
    """The frontier series in base-year dollars.

    Returns (year, real_cost_per_kg, deflator_is_provisional) per point.
    """
    ds = dataset or load_dataset()
    out = []
    for p in ds.frontier:
        # Deflate from price_year, not year. See FrontierPoint.
        real = to_real(p.cost_per_kg_leo, p.price_year, ds)
        out.append((p.year, real, ds.deflator.is_provisional(p.price_year)))
    return out


# ---------------------------------------------------------------------------
# 2. The decline rate
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class TrendFit:
    """OLS fit of log(cost) on year, plus what it implies.

    The specification is

        log(c_t) = alpha + beta * t + e_t

    so beta is a continuously-compounded annual growth rate and exp(beta) - 1
    is the annual percentage change. Logs are the right functional form because
    the claim being tested is about a constant *proportional* decline, not a
    constant dollar decline.
    """

    n: int
    alpha: float
    beta: float
    se_beta: float
    r_squared: float
    start_year: int
    end_year: int

    @property
    def annual_change(self) -> float:
        """Annual proportional change. Negative means falling."""
        return math.exp(self.beta) - 1

    @property
    def half_life_years(self) -> float | None:
        """Years for cost to halve at the fitted rate. None if not falling."""
        if self.beta >= 0:
            return None
        return math.log(0.5) / self.beta

    @property
    def t_stat(self) -> float | None:
        if self.se_beta == 0:
            return None
        return self.beta / self.se_beta

    def summary(self) -> str:
        direction = "fell" if self.beta < 0 else "rose"
        hl = (
            f", half-life {self.half_life_years:.1f} yr"
            if self.half_life_years is not None
            else ""
        )
        t = f"{self.t_stat:.2f}" if self.t_stat is not None else "n/a"
        return (
            f"{self.start_year}-{self.end_year} (n={self.n}): cost {direction} "
            f"{abs(self.annual_change):.1%}/yr{hl}. "
            f"beta={self.beta:.4f} (se {self.se_beta:.4f}, t={t}), "
            f"R2={self.r_squared:.3f}"
        )


def fit_log_linear_trend(points: list[tuple[int, float]]) -> TrendFit:
    """OLS of log(cost) on year, computed directly rather than via a library.

    beta_hat = sum((t - tbar)(y - ybar)) / sum((t - tbar)^2)
    sigma2   = RSS / (n - 2)
    se(beta) = sqrt(sigma2 / sum((t - tbar)^2))

    With a handful of anchor points the standard error is close to
    decorative: the points are chosen events, not a random sample, and the
    residuals are serially correlated by construction. Reported so the
    thinness is visible rather than hidden.
    """
    if len(points) < 3:
        raise ValueError("Need at least 3 points to fit a trend")

    years = [float(t) for t, _ in points]
    logs = [math.log(c) for _, c in points]
    n = len(points)

    tbar = sum(years) / n
    ybar = sum(logs) / n

    sxx = sum((t - tbar) ** 2 for t in years)
    sxy = sum((t - tbar) * (y - ybar) for t, y in zip(years, logs, strict=True))
    if sxx == 0:
        raise ValueError("All points share one year; slope is undefined")

    beta = sxy / sxx
    alpha = ybar - beta * tbar

    fitted = [alpha + beta * t for t in years]
    rss = sum((y - f) ** 2 for y, f in zip(logs, fitted, strict=True))
    tss = sum((y - ybar) ** 2 for y in logs)

    sigma2 = rss / (n - 2) if n > 2 else 0.0
    se_beta = math.sqrt(sigma2 / sxx) if sxx else 0.0
    r_squared = 1 - rss / tss if tss else 1.0

    return TrendFit(
        n=n,
        alpha=alpha,
        beta=beta,
        se_beta=se_beta,
        r_squared=r_squared,
        start_year=int(min(years)),
        end_year=int(max(years)),
    )


def frontier_trend(
    dataset: Dataset | None = None,
    *,
    real: bool = True,
    since: int | None = None,
) -> TrendFit:
    """Fit the frontier decline. Real dollars by default.

    `since` restricts to points at or after a year, which is how you see the
    structural break: the pre-2018 run and the post-2018 run are different
    regimes, and fitting one line through both averages them into a number
    that describes neither.
    """
    ds = dataset or load_dataset()
    pts: list[tuple[int, float]] = []
    for p in ds.frontier:
        if since is not None and p.year < since:
            continue
        cost = (
            to_real(p.cost_per_kg_leo, p.price_year, ds)
            if real
            else float(p.cost_per_kg_leo)
        )
        pts.append((p.year, cost))
    return fit_log_linear_trend(pts)


def endpoint_decline(dataset: Dataset | None = None, *, real: bool = True) -> dict:
    """The "cost fell Nx" headline, computed both ways.

    Included because the nominal and real answers differ enough to matter, and
    because the peak is a program-cost figure while the trough is a commercial
    list price, so the ratio is not a like-for-like comparison at all.
    """
    ds = dataset or load_dataset()
    series = [
        (p, to_real(p.cost_per_kg_leo, p.price_year, ds) if real else float(p.cost_per_kg_leo))
        for p in ds.frontier
    ]
    peak_pt, peak_val = max(series, key=lambda x: x[1])
    latest_pt, latest_val = series[-1]
    return {
        "basis": "real" if real else "nominal",
        "peak_year": peak_pt.year,
        "peak_vehicle": peak_pt.vehicle,
        "peak_cost_per_kg": round(peak_val),
        "peak_price_basis": peak_pt.price_basis.value,
        "latest_year": latest_pt.year,
        "latest_vehicle": latest_pt.vehicle,
        "latest_cost_per_kg": round(latest_val),
        "latest_price_basis": latest_pt.price_basis.value,
        "decline_factor": round(peak_val / latest_val, 1),
        "caveat": (
            f"Peak is a {peak_pt.price_basis.value} figure and the latest is a "
            f"{latest_pt.price_basis.value} figure. The ratio mixes bases."
        ),
    }


# ---------------------------------------------------------------------------
# 3. The access premium
# ---------------------------------------------------------------------------
def access_premium(dataset: Dataset | None = None) -> dict:
    """What a small customer pays relative to the frontier.

    The frontier assumes you buy the whole vehicle at its maximum expendable
    payload. A customer with a 50 kg satellite buys rideshare instead. The
    ratio between the two is the gap between the number in the headline and
    the number on the invoice.
    """
    ds = dataset or load_dataset()
    rideshare = ds.cheapest(basis=PriceBasis.RIDESHARE)
    dedicated = ds.cheapest(basis=PriceBasis.DEDICATED_LIST, operational_only=True)
    workhorse = ds.get("falcon-9-block-5")

    return {
        "rideshare_usd_per_kg": rideshare.cost_per_kg_leo,
        "rideshare_vehicle": rideshare.name,
        "frontier_usd_per_kg": dedicated.cost_per_kg_leo,
        "frontier_vehicle": dedicated.name,
        "premium_vs_frontier": round(
            rideshare.cost_per_kg_leo / dedicated.cost_per_kg_leo, 1
        ),
        "premium_vs_workhorse": round(
            rideshare.cost_per_kg_leo / workhorse.cost_per_kg_leo, 1
        ),
        "note": (
            "Both figures are published SpaceX prices from the same year, so "
            "this comparison holds the provider, the vehicle family and the "
            "price year fixed. The gap is the cost of not filling a rocket."
        ),
    }
