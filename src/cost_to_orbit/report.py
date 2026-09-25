"""Print the three findings from the README, computed from the data.

    python -m cost_to_orbit.report

Exists so the numbers in the README are reproducible rather than asserted. If
the data changes, this output changes, and the README should be updated to
match it.
"""

from __future__ import annotations

from cost_to_orbit import analysis
from cost_to_orbit.dataset import load_dataset


def _rule(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def main() -> int:
    ds = load_dataset()
    base = ds.deflator.base_year

    print(f"Cost-to-Orbit findings   (data last verified {ds.last_verified})")

    _rule("1. Deflating changes the headline")
    for real in (False, True):
        d = analysis.endpoint_decline(ds, real=real)
        label = f"real {base} USD" if real else "nominal"
        print(
            f"  {label:>14}: ${d['peak_cost_per_kg']:>8,}/kg ({d['peak_year']}) "
            f"-> ${d['latest_cost_per_kg']:>6,}/kg ({d['latest_year']})  = {d['decline_factor']}x"
        )
    print(f"  caveat: {analysis.endpoint_decline(ds)['caveat']}")

    _rule(f"2. Log-linear trend, real {base} USD")
    print(f"  full sample : {analysis.frontier_trend(ds, real=True).summary()}")
    print(f"  since 2010  : {analysis.frontier_trend(ds, real=True, since=2010).summary()}")

    _rule(f"   Frontier series, real {base} USD")
    for year, cost, provisional in analysis.real_frontier(ds):
        flag = "  (provisional deflator)" if provisional else ""
        print(f"     {year}  ${round(cost):>8,}/kg{flag}")

    _rule("3. The access premium")
    a = analysis.access_premium(ds)
    print(f"  {a['frontier_vehicle']:<34} ${a['frontier_usd_per_kg']:>6,}/kg")
    print(f"  {'Falcon 9 dedicated':<34} ${ds.get('falcon-9-block-5').cost_per_kg_leo:>6,}/kg")
    print(f"  {a['rideshare_vehicle']:<34} ${a['rideshare_usd_per_kg']:>6,}/kg")
    print(f"  premium over frontier: {a['premium_vs_frontier']}x   "
          f"over Falcon 9 dedicated: {a['premium_vs_workhorse']}x")

    _rule("Excluded and flagged")
    for v in ds.unpriced():
        print(f"  unpriced        {v.name}")
    for v in ds.low_confidence():
        print(f"  low confidence  {v.name}")
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
