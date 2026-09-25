"""Loading and querying the dataset.

Everything reads through `load_dataset()`, which validates the JSON against the
models in `models.py`. If the data is malformed, this raises at import time in
whatever is using it, which is the point.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from cost_to_orbit.models import (
    Confidence,
    Deflator,
    FrontierPoint,
    PriceBasis,
    Status,
    Vehicle,
)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


@dataclass(frozen=True)
class Dataset:
    """The validated dataset plus the query helpers worth having."""

    vehicles: tuple[Vehicle, ...]
    frontier: tuple[FrontierPoint, ...]
    deflator: Deflator
    methodology: dict
    series_definition: dict
    last_verified: str

    # -- selection ---------------------------------------------------------
    def get(self, vehicle_id: str) -> Vehicle:
        for v in self.vehicles:
            if v.id == vehicle_id:
                return v
        raise KeyError(f"No vehicle with id {vehicle_id!r}")

    def select(
        self,
        *,
        basis: PriceBasis | str | None = None,
        status: Status | str | None = None,
        country: str | None = None,
        min_confidence: Confidence | str | None = None,
        priced_only: bool = False,
        operational_only: bool = False,
    ) -> list[Vehicle]:
        """Filter the cross-section.

        `basis` is the filter that matters most. Any statistic computed across
        mixed price bases is comparing a commercial sticker price to a
        government programme's total cost, which is not a comparison.
        """
        rank = {Confidence.LOW: 0, Confidence.MEDIUM: 1, Confidence.HIGH: 2}
        rows = list(self.vehicles)

        if basis is not None:
            basis = PriceBasis(basis)
            rows = [v for v in rows if v.price_basis == basis]
        if status is not None:
            status = Status(status)
            rows = [v for v in rows if v.status == status]
        if country is not None:
            rows = [v for v in rows if country.lower() in v.country.lower()]
        if min_confidence is not None:
            floor = rank[Confidence(min_confidence)]
            rows = [v for v in rows if rank[v.confidence] >= floor]
        if priced_only:
            rows = [v for v in rows if v.cost_per_kg_leo is not None]
        if operational_only:
            rows = [v for v in rows if v.is_operational]
        return rows

    def cheapest(self, **kwargs) -> Vehicle:
        """Cheapest $/kg among rows matching the filter."""
        rows = self.select(priced_only=True, **kwargs)
        if not rows:
            raise ValueError("No priced vehicles match that filter")
        return min(rows, key=lambda v: v.cost_per_kg_leo)

    def most_expensive(self, **kwargs) -> Vehicle:
        rows = self.select(priced_only=True, **kwargs)
        if not rows:
            raise ValueError("No priced vehicles match that filter")
        return max(rows, key=lambda v: v.cost_per_kg_leo)

    # -- integrity ---------------------------------------------------------
    def unpriced(self) -> list[Vehicle]:
        """Rows carrying no price. Excluded from every $/kg statistic."""
        return [v for v in self.vehicles if v.cost_per_kg_leo is None]

    def low_confidence(self) -> list[Vehicle]:
        return [v for v in self.vehicles if v.confidence == Confidence.LOW]


def _read(name: str) -> dict:
    with open(DATA_DIR / name) as f:
        return json.load(f)


@lru_cache(maxsize=1)
def load_dataset() -> Dataset:
    """Load, validate and cache the dataset."""
    raw_vehicles = _read("vehicles.json")
    raw_frontier = _read("historical.json")
    raw_deflator = _read("deflator.json")

    deflator = Deflator(
        series=raw_deflator["series"],
        source=raw_deflator["source"],
        source_url=raw_deflator.get("source_url"),
        base_year=raw_deflator["base_year"],
        note=raw_deflator.get("note"),
        values={int(y): v for y, v in raw_deflator["values"].items()},
        provisional_years=raw_deflator.get("provisional_years", []),
    )

    return Dataset(
        vehicles=tuple(Vehicle(**v) for v in raw_vehicles["vehicles"]),
        frontier=tuple(FrontierPoint(**p) for p in raw_frontier["points"]),
        deflator=deflator,
        methodology=raw_vehicles["methodology"],
        series_definition=raw_frontier["series_definition"],
        last_verified=raw_vehicles["last_verified"],
    )
