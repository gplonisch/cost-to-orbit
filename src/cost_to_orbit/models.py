"""Typed schema for the dataset.

Every row that enters the dataset is validated against these models, so a typo
in the JSON fails loudly at load time rather than silently producing a wrong
chart three steps later. The validators encode the rules that actually matter
for this data: a stored $/kg must equal price / payload, and a row that claims
a price must say what kind of price it is.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, Field, model_validator

# Stored $/kg values are rounded to the dollar, so allow a small relative gap
# between the stored figure and the recomputed one before calling it an error.
ROUNDING_TOLERANCE = 0.02


class PriceBasis(StrEnum):
    """What kind of number the price actually is.

    This is the field that makes the dataset defensible. Most public $/kg
    charts silently mix a commercial list price, a government contract price
    and a total-program-cost-per-flight figure into one series, which is how
    the Space Shuttle ends up "costing" thirty times a Falcon 9 in a way that
    is true but not a like-for-like comparison. Keeping the basis explicit
    means any statistic can be computed within a basis instead of across them.
    """

    DEDICATED_LIST = "dedicated_list"
    RIDESHARE = "rideshare"
    GOV_CONTRACT = "gov_contract"
    PROGRAM_COST = "program_cost"
    ESTIMATE = "estimate"


class Confidence(StrEnum):
    """How much weight the underlying figure can carry."""

    HIGH = "high"      # published commercial price
    MEDIUM = "medium"  # credible reporting or a government audit
    LOW = "low"        # estimate, contested figure, or a basis/currency mismatch


class Status(StrEnum):
    ACTIVE = "active"
    RETIRING = "retiring"
    RETIRED = "retired"
    DEVELOPMENT = "development"
    PROJECTED = "projected"


PositiveUSD = Annotated[int, Field(gt=0)]
PositiveKg = Annotated[int, Field(gt=0)]


class Vehicle(BaseModel):
    """One launch vehicle, or one purchasable launch service."""

    id: str
    name: str
    provider: str
    country: str
    first_flight: int | None = None
    retired_year: int | None = None
    status: Status
    reusable: str

    payload_leo_kg: PositiveKg | None = None
    payload_gto_kg: PositiveKg | None = None

    price_usd: PositiveUSD | None = None
    price_usd_low: PositiveUSD | None = None
    price_usd_high: PositiveUSD | None = None
    price_year: int | None = None
    price_basis: PriceBasis | None = None

    cost_per_kg_leo: int | None = None
    confidence: Confidence
    source: str
    source_url: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _check_cost_is_derived(self) -> Vehicle:
        """The stored $/kg must equal price / payload. No hand-typed figures."""
        if self.price_usd is not None and self.payload_leo_kg:
            recomputed = round(self.price_usd / self.payload_leo_kg)
            if self.cost_per_kg_leo is None:
                raise ValueError(
                    f"{self.id}: has price and payload but cost_per_kg_leo is null"
                )
            drift = abs(recomputed - self.cost_per_kg_leo) / recomputed
            if drift > ROUNDING_TOLERANCE:
                raise ValueError(
                    f"{self.id}: cost_per_kg_leo is {self.cost_per_kg_leo:,} but "
                    f"price/payload gives {recomputed:,} ({drift:.1%} off)"
                )
        elif self.cost_per_kg_leo is not None:
            raise ValueError(
                f"{self.id}: has cost_per_kg_leo but no price and payload to derive it from"
            )
        return self

    @model_validator(mode="after")
    def _check_priced_rows_state_their_basis(self) -> Vehicle:
        if self.price_usd is not None and self.price_basis is None:
            raise ValueError(f"{self.id}: has a price but no price_basis")
        return self

    @model_validator(mode="after")
    def _check_estimate_range(self) -> Vehicle:
        lo, hi = self.price_usd_low, self.price_usd_high
        if (lo is None) != (hi is None):
            raise ValueError(f"{self.id}: price range needs both low and high, or neither")
        if lo is not None and hi is not None:
            if lo > hi:
                raise ValueError(f"{self.id}: price_usd_low exceeds price_usd_high")
            if self.price_usd is not None and not (lo <= self.price_usd <= hi):
                raise ValueError(
                    f"{self.id}: price_usd {self.price_usd:,} sits outside its stated "
                    f"range {lo:,}-{hi:,}"
                )
        return self

    @property
    def is_operational(self) -> bool:
        return self.status in (Status.ACTIVE, Status.RETIRING)


class FrontierPoint(BaseModel):
    """One anchor point on the frontier-cost series.

    `year` and `price_year` are different things and keeping them apart is the
    whole reason this model exists. `year` is when the vehicle reset the
    frontier. `price_year` is the dollar basis of the figure, which often comes
    from a much later source: the 1981 Space Shuttle number is a program-cost
    estimate published in 2008 dollars. Deflating it from 1981 rather than 2008
    inflates the real peak by more than a factor of two, which is exactly the
    kind of error this dataset exists to avoid.
    """

    year: int
    price_year: int
    cost_per_kg_leo: PositiveUSD
    vehicle: str
    vehicle_id: str | None = None
    price_basis: PriceBasis
    confidence: Confidence
    note: str | None = None


class Deflator(BaseModel):
    """CPI-U index used to convert nominal dollars to a common base year."""

    series: str
    source: str
    source_url: str | None = None
    base_year: int
    note: str | None = None
    values: dict[int, float]
    provisional_years: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_base_year_present(self) -> Deflator:
        if self.base_year not in self.values:
            raise ValueError(f"base_year {self.base_year} is missing from the index")
        return self

    def factor(self, from_year: int) -> float:
        """Multiplier that converts `from_year` dollars into base-year dollars."""
        if from_year not in self.values:
            raise KeyError(
                f"No CPI value for {from_year}. Available: "
                f"{min(self.values)}-{max(self.values)}"
            )
        return self.values[self.base_year] / self.values[from_year]

    def is_provisional(self, year: int) -> bool:
        return year in self.provisional_years
