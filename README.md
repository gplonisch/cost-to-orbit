# Cost-to-Orbit

A sourced dataset of launch price per kilogram to low Earth orbit, built so that
the price basis of every number stays visible.

[![CI](https://github.com/gplonisch/cost-to-orbit/actions/workflows/ci.yml/badge.svg)](https://github.com/gplonisch/cost-to-orbit/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![License](https://img.shields.io/badge/code-MIT-green)
![Data](https://img.shields.io/badge/data-CC--BY--4.0-green)

Falling launch cost is the premise of most space-economy analysis. The number
usually cited for it is assembled badly. This repository is an attempt to
assemble it carefully and to publish what it still gets wrong.

## The problem with the usual chart

Nearly every published $/kg-to-orbit comparison mixes three different kinds of
number into one series:

- a commercial list price, which is what SpaceX will sell you a rocket for
- a government contract price, which includes mission assurance a commercial
  buyer never purchases
- a total-program-cost-per-flight figure, which includes development

The Space Shuttle appears on these charts at roughly $54,000/kg. That is its
program cost divided by its payload. Falcon Heavy appears at $1,520/kg, which is
a sticker price. The 36x ratio between them is real arithmetic and a bad
comparison, because it attributes to reusability a gap that is mostly the
difference between counting development cost and not counting it.

Two further problems compound it. The figures are nominal, so a 1981 number and
a 2026 number are in different dollars. And the frontier price assumes you buy an
entire Falcon Heavy at its maximum expendable payload, which no customer has ever
done.

This dataset carries a `price_basis` field on every row, stores a CPI-U deflator
alongside the prices, and includes the rideshare price a small customer actually
pays. Statistics are computed within a basis, not across them.

## Three findings

All figures are computed live from the data by `cost_to_orbit.analysis`; run
`make analysis` to reproduce them.

### 1. Deflating raises the decline from 36x to 55x

| Basis | Peak | Latest | Decline |
|---|---|---|---|
| Nominal | $54,545/kg (1981) | $1,520/kg (2026) | 36x |
| Real, 2026 USD | $83,604/kg (1981) | $1,520/kg (2026) | 55x |

Getting this right requires separating two years that are easy to conflate. The
Shuttle reset the frontier in 1981, but the $54,545/kg figure comes from a
program-cost estimate published in 2008 dollars. Deflating it from 1981 gives
$198,018/kg and a 130x decline, which is wrong by more than a factor of two.
Every frontier point therefore carries both a `year` and a `price_year`, and
the deflation uses `price_year`.

The remaining caveat is not fixable by arithmetic: the peak is a program-cost
figure and the trough is a list price, so neither ratio is like-for-like.

### 2. The frontier went backwards for 25 years, which is why one trend line does not fit it

Fitting log(cost) on year over the real series:

```
1967-2026 (n=6): cost fell 4.6%/yr, half-life 14.7 yr. beta=-0.0471 (se 0.0218, t=-2.16), R2=0.539
2010-2026 (n=3): cost fell 9.7%/yr, half-life 6.8 yr. beta=-0.1024 (se 0.0447, t=-2.29), R2=0.840
```

The full-sample R2 of 0.54 is the finding, not a defect. Real frontier cost was
about $10,600/kg in 1967 and about $83,600/kg in 1981. The Shuttle made access
to orbit roughly eight times more expensive and held it there for a quarter
century. A single exponential fitted through that is describing an average of
two regimes and representing neither.

| Year | Real 2026 $/kg | Vehicle |
|---|---|---|
| 1967 | $10,566 | Saturn V |
| 1981 | $83,604 | Space Shuttle |
| 2006 | $11,161 | Atlas V 551 |
| 2010 | $7,818 | Falcon 9 v1.0 |
| 2018 | $1,854 | Falcon Heavy |
| 2026 | $1,520 | Falcon Heavy |

Since 2018 the nominal frontier has risen, from $1,411/kg to $1,520/kg, because
SpaceX raised list prices for inflation and nobody undercut them. In real terms
the same period is a fall of about 2.5%/yr. Both statements come from the same
two prices; only the deflator differs, which is why the deflator is a data file
in this repository rather than a constant in a script.

### 3. A small customer pays 4.6x the frontier price

| What you buy | $/kg to LEO |
|---|---|
| Falcon Heavy, max expendable payload | $1,520 |
| Falcon 9, dedicated, max expendable payload | $3,246 |
| Falcon 9 Transporter rideshare | $7,000 |

Same provider, same vehicle family, same year, so the comparison holds
everything but the purchase size fixed. The gap is the cost of not filling a
rocket. Most analysis of the space economy quotes the first row and models
behaviour that responds to the third.

## What the dataset does not know

Published in the repo and served at `/integrity` rather than buried:

- Starship carries no price. It began deploying operational payloads in 2026,
  but no customer can buy a launch at a published rate, so it is excluded from
  every statistic here. Stated targets of $100-200/kg are design goals, not
  prices. Including them in cost curves is the most common error in this field.
- New Glenn has flown but Blue Origin publishes no list price. The $110M figure
  is the conservative end of a reported $68-110M range and is marked low
  confidence.
- Ariane 6 is the weakest row: a 2018 euro-denominated estimate, converted at a
  fixed rate, for a vehicle that first flew in 2024.
- The Long March 5 figure is an estimate of a state-directed price, which is not
  a market-clearing price and carries little economic information.
- The frontier series has six anchor points. The reported standard errors are
  close to decorative, since the points are chosen events rather than a random
  sample and the residuals are serially correlated by construction. They are
  reported so the thinness is visible.
- The 2025 and 2026 CPI values are provisional.

## Layout

```
data/
  vehicles.json     16 vehicles and services, each with price_basis and a source URL
  historical.json   frontier anchor points, nominal
  deflator.json     CPI-U index, so deflation is auditable instead of baked in
  SOURCES.md        per-number provenance and the methodology choices
src/cost_to_orbit/
  models.py         pydantic schema; validators enforce cost == price / payload
  dataset.py        loading and filtering
  analysis.py       deflation, the log-linear trend, the access premium
  api.py            read-only FastAPI service
  validate.py       standalone integrity check
tests/              schema, arithmetic, analysis and API tests
dashboard/          single-file Chart.js front end
```

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[api,dev]"

pytest                                   # tests
cost-to-orbit-validate                   # data integrity check
uvicorn cost_to_orbit.api:app --reload   # API at /docs, dashboard at /app
```

The API is open by default. Set `COST_TO_ORBIT_API_KEYS` to a comma-separated
list to require an `X-API-Key` header. Keys are read from the environment, never
from a file in the repository.

```python
from cost_to_orbit import load_dataset
from cost_to_orbit import analysis

ds = load_dataset()
ds.cheapest(basis="dedicated_list", operational_only=True).name   # 'Falcon Heavy'
analysis.frontier_trend(ds, real=True).summary()
analysis.access_premium(ds)["premium_vs_frontier"]                # 4.6
```

## Methodology

`cost_per_kg_leo = price_usd / payload_leo_kg`, where payload is the maximum
advertised payload to a reference LEO in expendable configuration. That is the
convention used in public comparisons, and it flatters reusable vehicles, which
in practice fly well below their expendable ceiling.

Deflation uses CPI-U, U.S. city average, all items, annual average. CPI-U is the
right index for prices paid rather than output deflated. A GDP deflator or a
capital-goods PPI would be defensible alternatives and would move the pre-2000
figures noticeably.

Full per-number provenance is in [data/SOURCES.md](data/SOURCES.md). Every row
carries a `source_url`. Prices were last verified on 2026-09-24.

## Contributing a correction

Corrections to the data are the most useful contribution. Open an issue with the
vehicle id, the figure you believe is wrong, and a source. Rows are expected to
change; the point of the schema is that a changed price forces a changed
`cost_per_kg_leo`, and the validator will fail the build if it does not.

## License

Code is MIT. Data in `data/` is CC BY 4.0 — use it, cite it. See [LICENSE](LICENSE).
