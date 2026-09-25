"""Standalone integrity check for the dataset.

    cost-to-orbit-validate

Loading the dataset already validates the schema, because the pydantic models
enforce that every stored $/kg equals price / payload. This adds the checks that
are about the dataset as a whole rather than any single row, and prints the
things a maintainer should keep an eye on. It exits non-zero on error so CI
fails when the data drifts.
"""

from __future__ import annotations

import sys

from cost_to_orbit.dataset import load_dataset
from cost_to_orbit.models import Confidence, PriceBasis


def main() -> int:
    errors: list[str] = []
    notes: list[str] = []

    try:
        ds = load_dataset()
    except Exception as exc:  # schema failures surface here
        print(f"FAILED to load dataset:\n  {exc}")
        return 1

    ids = [v.id for v in ds.vehicles]
    for dup in {i for i in ids if ids.count(i) > 1}:
        errors.append(f"duplicate vehicle id: {dup}")

    for v in ds.vehicles:
        if v.price_usd is not None and v.price_year is None:
            errors.append(f"[{v.id}] has a price but no price_year")
        if v.price_year is not None and v.price_year not in ds.deflator.values:
            errors.append(
                f"[{v.id}] price_year {v.price_year} has no CPI value, so this row "
                f"cannot be deflated"
            )
        if v.retired_year and v.first_flight and v.retired_year < v.first_flight:
            errors.append(f"[{v.id}] retired before it first flew")
        if v.confidence == Confidence.HIGH and v.price_basis == PriceBasis.ESTIMATE:
            errors.append(f"[{v.id}] an estimate cannot be high confidence")
        if v.source_url is None:
            notes.append(f"[{v.id}] no source_url")

    for p in ds.frontier:
        if p.price_year not in ds.deflator.values:
            errors.append(
                f"frontier point {p.year} has price_year {p.price_year} with no CPI "
                f"value, so it cannot be deflated"
            )
        if p.vehicle_id is not None and p.vehicle_id not in ids:
            errors.append(f"frontier point {p.year} references unknown vehicle {p.vehicle_id!r}")

    years = [p.year for p in ds.frontier]
    if years != sorted(years):
        errors.append("frontier points are not in ascending year order")

    print(f"Cost-to-Orbit dataset, last verified {ds.last_verified}")
    print(f"  {len(ds.vehicles)} vehicles, {len(ds.frontier)} frontier points\n")

    unpriced = ds.unpriced()
    if unpriced:
        print(f"Unpriced, excluded from all statistics ({len(unpriced)}):")
        for v in unpriced:
            print(f"  - {v.name}")
        print()

    low = ds.low_confidence()
    if low:
        print(f"Low confidence, verify against a primary source ({len(low)}):")
        for v in low:
            print(f"  - {v.name}")
        print()

    if ds.deflator.provisional_years:
        print(f"Provisional CPI years: {ds.deflator.provisional_years}\n")

    if notes:
        print(f"Notes ({len(notes)}):")
        for n in notes:
            print(f"  - {n}")
        print()

    if errors:
        print(f"ERRORS ({len(errors)}):")
        for e in errors:
            print(f"  - {e}")
        print("\nFAILED")
        return 1

    print("All integrity checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
