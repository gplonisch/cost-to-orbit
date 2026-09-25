"""Regenerate data/SOURCES.md from the dataset.

    python scripts/build_sources.py

The provenance table is generated rather than hand-maintained so it cannot
drift away from the data it documents. tests/test_sources.py fails if the
committed file is stale.
"""

from __future__ import annotations

import sys
from pathlib import Path

from cost_to_orbit.dataset import load_dataset

ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "data" / "SOURCES.md"

PREAMBLE = """# Sources and methodology

Generated from `data/vehicles.json` by `scripts/build_sources.py`. Do not edit
by hand; edit the data and regenerate.

The product here is not the chart. Anyone can assert that launch cost is
falling. What is scarce is one series where every number states its basis, its
dollar year, and where it came from, so a reader can disagree with a specific
figure rather than with the whole thing.

## The formula

    cost_per_kg_leo = price_usd / payload_leo_kg

`payload_leo_kg` is the maximum advertised payload to a reference low Earth
orbit in expendable configuration. This is the convention used in public
comparisons. It flatters reusable vehicles, which in practice fly well below
their expendable ceiling, so the figures here are a floor on what anyone
actually pays per kilogram.

## Why price_basis exists

A launch price can be any of five different things, and public $/kg charts
routinely average across them:

| Basis | What it is | Comparable to |
|---|---|---|
| `dedicated_list` | Published commercial price for a dedicated launch | Other list prices |
| `rideshare` | Published per-kg price for a shared launch | Other rideshare prices |
| `gov_contract` | Reported government contract price | Other contract prices |
| `program_cost` | Total programme cost divided by flights flown | Other programme costs |
| `estimate` | No published price; analyst estimate or reported range | Treat as indicative |

The Space Shuttle's famous $54,545/kg is `program_cost`, which includes three
decades of development. Falcon Heavy's $1,520/kg is `dedicated_list`, which
includes none. Both numbers are correct. Dividing one by the other is not a
measure of anything.

## Dollar years

Prices are nominal in their stated `price_year`. Deflation is applied in code
using `data/deflator.json` (CPI-U, U.S. city average, all items, annual
average) rather than stored, so the index is visible and replaceable.

The frontier series in `data/historical.json` carries both a `year` and a
`price_year`. These differ: the Space Shuttle reset the frontier in 1981, but
the cost estimate attached to it is published in 2008 dollars. Deflating from
`year` instead of `price_year` inflates the real 1981 peak from about
$83,600/kg to about $198,000/kg and turns a 55x decline into a 130x one.

## Confidence

| Level | Meaning |
|---|---|
| `high` | Published commercial price from the provider |
| `medium` | Credible reporting, government audit, or a widely-corroborated figure |
| `low` | Estimate, contested figure, or a basis or currency mismatch |

"""


def build() -> str:
    ds = load_dataset()
    out = [PREAMBLE, f"## Per-vehicle provenance\n\nPrices last verified {ds.last_verified}.\n"]

    out.append("| Vehicle | $/kg LEO | Price | Year | Basis | Confidence | Source |")
    out.append("|---|---|---|---|---|---|---|")
    for v in sorted(ds.vehicles, key=lambda v: (v.cost_per_kg_leo is None, v.cost_per_kg_leo or 0)):
        cost = f"${v.cost_per_kg_leo:,}" if v.cost_per_kg_leo is not None else "not priced"
        if v.price_usd is None:
            price = "n/a"
        elif v.price_usd_low is not None and v.price_usd_low != v.price_usd_high:
            price = f"${v.price_usd/1e6:,.1f}M (range ${v.price_usd_low/1e6:,.0f}-{v.price_usd_high/1e6:,.0f}M)"
        else:
            price = f"${v.price_usd/1e6:,.2f}M"
        year = v.price_year or "n/a"
        basis = f"`{v.price_basis}`" if v.price_basis else "n/a"
        src = f"[{v.source}]({v.source_url})" if v.source_url else v.source
        out.append(
            f"| {v.name} | {cost} | {price} | {year} | {basis} | {v.confidence} | {src} |"
        )

    out.append("\n## Row-level notes\n")
    for v in ds.vehicles:
        if v.notes:
            out.append(f"**{v.name}** — {v.notes}\n")

    out.append("## Frontier series\n")
    out.append("| Anchor year | $/kg (nominal) | Dollar year | Vehicle | Basis | Confidence |")
    out.append("|---|---|---|---|---|---|")
    for p in ds.frontier:
        out.append(
            f"| {p.year} | ${p.cost_per_kg_leo:,} | {p.price_year} | {p.vehicle} | "
            f"`{p.price_basis}` | {p.confidence} |"
        )

    out.append("\n### Frontier notes\n")
    for p in ds.frontier:
        if p.note:
            out.append(f"**{p.year}, {p.vehicle}** — {p.note}\n")

    out.append("## Known weaknesses\n")
    out.append(
        "Published here rather than buried, because a dataset that does not say "
        "what it is unsure about is asking to be trusted more than it deserves.\n"
    )
    for v in ds.low_confidence():
        out.append(f"- **{v.name}** — {v.source}")
    out.append(
        f"\n- The frontier series has only {len(ds.frontier)} anchor points, so any "
        "standard error computed from it is close to decorative."
    )
    out.append(
        f"- CPI values for {ds.deflator.provisional_years} are provisional and should be "
        "refreshed from BLS once the annual averages are final."
    )
    return "\n".join(out) + "\n"


def main() -> int:
    TARGET.write_text(build())
    print(f"wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
