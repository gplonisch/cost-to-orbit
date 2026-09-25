# Sources and methodology

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


## Per-vehicle provenance

Prices last verified 2026-09-24.

| Vehicle | $/kg LEO | Price | Year | Basis | Confidence | Source |
|---|---|---|---|---|---|---|
| Falcon Heavy | $1,520 | $97.00M | 2026 | `dedicated_list` | high | [SpaceX published list price, ~$97M dedicated, 2026](https://www.spacex.com/assets/media/Capabilities&Services.pdf) |
| New Glenn | $2,444 | $110.0M (range $68-110M) | 2026 | `estimate` | low | [Blue Origin has not published a list price. Reported estimates span $68-110M; the upper bound is used here as the conservative figure.](https://en.wikipedia.org/wiki/New_Glenn) |
| Falcon 9 Block 5 | $3,246 | $74.00M | 2026 | `dedicated_list` | high | [SpaceX published list price, $74M standard payment plan for 2026 (up from $70M in 2025, $69.75M in 2024, $67M in 2022, $62M in 2018)](https://www.spacex.com/assets/media/Capabilities&Services.pdf) |
| Neutron | $3,846 | $50.00M | 2026 | `estimate` | low | [Rocket Lab announced target price ~$50M per launch; vehicle has not flown](https://en.wikipedia.org/wiki/Rocket_Lab_Neutron) |
| Vulcan Centaur (VC6) | $4,044 | $110.00M | 2025 | `dedicated_list` | medium | [ULA reported starting price ~$110M](https://en.wikipedia.org/wiki/Vulcan_Centaur) |
| PSLV-XL | $5,526 | $21.0M (range $16-24M) | 2023 | `dedicated_list` | medium | [Rs 130-200 crore, approx $16-24M (2023); ~$21M commonly cited for PSLV-XL](https://en.wikipedia.org/wiki/Polar_Satellite_Launch_Vehicle) |
| Ariane 6 (A64) | $5,737 | $124.20M | 2018 | `estimate` | low | [EUR 115M per-launch estimate (2018), converted at 1.08 USD/EUR. Arianespace does not publish per-flight pricing.](https://en.wikipedia.org/wiki/Ariane_6) |
| Long March 5 | $6,400 | $160.00M | 2023 | `estimate` | low | [Estimated ~$160M per launch; Chinese pricing is not publicly listed](https://en.wikipedia.org/wiki/Long_March_5) |
| Falcon 9 (Transporter rideshare) | $7,000 | $0.35M | 2026 | `rideshare` | high | [SpaceX Smallsat Rideshare Program published pricing, $350,000 for 50 kg to SSO, $7,000/kg beyond (Transporter-16 onward, 2026)](https://www.spacex.com/rideshare) |
| Atlas V 551 | $8,117 | $153.0M (range $110-153M) | 2016 | `gov_contract` | medium | [Reported cost per launch $110-153M (2016); upper bound used for the 551 configuration](https://en.wikipedia.org/wiki/Atlas_V) |
| Saturn V | $8,286 | $1,160.00M | 2020 | `program_cost` | low | [Inflation-adjusted per-launch cost; ~$185M nominal 1969, variously adjusted to $1.0-1.5B depending on dollar-year and allocation of development cost](https://en.wikipedia.org/wiki/Saturn_V) |
| Ariane 5 ECA | $8,476 | $178.00M | 2020 | `dedicated_list` | medium | [Reported Arianespace commercial pricing, ~$178M](https://en.wikipedia.org/wiki/Ariane_5) |
| Soyuz-2 (Soyuz-ST, Kourou) | $9,756 | $80.0M (range $35-80M) | 2018 | `dedicated_list` | low | [Arianespace commercial Soyuz-ST at Kourou ~$80M; domestic Roscosmos launches reported as low as ~$35M](https://en.wikipedia.org/wiki/Soyuz-2) |
| Delta IV Heavy | $12,158 | $350.00M | 2019 | `gov_contract` | medium | [Reported per-launch cost ~$350M; NRO missions reported at ~$440M](https://en.wikipedia.org/wiki/Delta_IV_Heavy) |
| Space Shuttle | $54,545 | $1,500.00M | 2008 | `program_cost` | medium | [Total program cost averaged over all missions, inflation-adjusted to 2008 USD, ~$1.5B per launch; total program spend ~$196B through 2011](https://en.wikipedia.org/wiki/Space_Shuttle) |
| Starship | not priced | n/a | n/a | n/a | low | [Began deploying operational payloads in 2026; no published commercial price](https://en.wikipedia.org/wiki/SpaceX_Starship) |

## Row-level notes

**Falcon Heavy** — Lowest list $/kg of any operational vehicle, but only at max fully-expendable payload, which no customer has ever actually bought. Treat as a theoretical floor.

**New Glenn** — First flight 16 Jan 2025 (NG-1, reached orbit). First booster recovery on NG-3, 19 Apr 2026. A pad anomaly during a hotfire test at LC-36 on 28 May 2026 interrupted the flight campaign. Range is wide because no price is published; at the low end this vehicle would beat Falcon 9.

**Falcon 9 Block 5** — Nominal list price has risen roughly 19% since 2018 even as the frontier narrative says launch is getting cheaper. Both are true: the frontier fell because Falcon Heavy and reuse arrived, not because Falcon 9's sticker price fell.

**Neutron** — PROJECTED. Debut slipped repeatedly; as of Aug 2026 the window for a 2026 first flight was reported as narrowing. Excluded from active-vehicle statistics.

**Vulcan Centaur (VC6)** — Price is the starting figure; actual price varies substantially with solid booster count. VC6 is the six-booster maximum configuration, so pairing the max payload with the starting price flatters this row.

**PSLV-XL** — Workhorse for sun-synchronous and small missions. Low absolute price, modest payload. Domestic Indian cost structure is not directly comparable to Western commercial pricing.

**Ariane 6 (A64)** — Weakest row in the dataset and flagged as such. The underlying figure is a 2018 euro-denominated estimate for a vehicle that first flew in 2024, carried here in nominal converted dollars. Do not treat as a current price.

**Long March 5** — Not sold to Western customers, so there is no market-clearing price to observe. State-directed pricing makes the $/kg figure close to meaningless as an economic signal.

**Falcon 9 (Transporter rideshare)** — This is the single most useful row in the dataset and the one most often left out of $/kg charts. A small customer buying access today pays about 2.2x the Falcon 9 dedicated max-payload rate and 4.6x the Falcon Heavy rate. The frontier number is not the transacted number.

**Atlas V 551** — Most powerful Atlas V variant, phased out for Vulcan. Government contract pricing includes mission assurance a commercial customer does not buy.

**Ariane 5 ECA** — Dual-GTO workhorse. Retired in favour of Ariane 6, which on current estimates is not dramatically cheaper per kg.

**Saturn V** — Highest payload ever flown. Published estimates range roughly $6,300-8,800/kg depending on dollar-year and payload assumption. Heavily contested; included for historical perspective only.

**Soyuz-2 (Soyuz-ST, Kourou)** — Basis mismatch flagged: the price is the Kourou commercial figure while the payload is the standard Soyuz-2.1b LEO figure, so this row mixes two configurations. Western commercial availability ended in 2022; status reflects commercial availability, not Russian domestic flights, which continue.

**Delta IV Heavy** — Most expensive Western vehicle per launch. Flew high-value national security payloads where schedule assurance dominated price.

**Space Shuttle** — Program-cost basis, which is why it towers over every other row. Marginal per-flight cost was far lower (~$450M). The honest comparison is program cost to program cost, and almost nobody makes it. Reusability pursued without cheap refurbishment.

**Starship** — NO PRICE. Stated targets range from $100-200/kg (Musk, May 2026) to internal per-launch cost estimates around $25M, but none of these is a price a customer can buy at. Deliberately excluded from every $/kg statistic in this repository. Including aspirational targets in cost curves is the most common error in launch-cost analysis.

## Frontier series

| Anchor year | $/kg (nominal) | Dollar year | Vehicle | Basis | Confidence |
|---|---|---|---|---|---|
| 1967 | $8,286 | 2020 | Saturn V | `program_cost` | low |
| 1981 | $54,545 | 2008 | Space Shuttle | `program_cost` | medium |
| 2006 | $8,117 | 2016 | Atlas V 551 | `gov_contract` | medium |
| 2010 | $5,167 | 2010 | Falcon 9 v1.0 | `dedicated_list` | medium |
| 2018 | $1,411 | 2018 | Falcon Heavy | `dedicated_list` | medium |
| 2026 | $1,520 | 2026 | Falcon Heavy | `dedicated_list` | high |

### Frontier notes

**1967, Saturn V** — Inflation-adjusted program cost per launch over 140 t payload. Contested; estimates span roughly $6,300-8,800/kg.

**1981, Space Shuttle** — Program cost per flight in 2008 USD over 27.5 t payload. The frontier moved backwards: reusability without cheap refurbishment.

**2006, Atlas V 551** — EELV-era expendable frontier. Price figure is 2016 reported cost applied to the 2006 debut, so this point is dated later than its anchor year.

**2010, Falcon 9 v1.0** — Derived: ~$54M list over 10,450 kg LEO. SpaceX enters and undercuts incumbents on expendable pricing alone, before reuse.

**2018, Falcon Heavy** — Derived: ~$90M debut list price over 63,800 kg. Falcon 9 Block 5 in the same year was ~$2,719/kg at a $62M list price.

**2026, Falcon Heavy** — Derived: $97M list over 63,800 kg. The nominal frontier has RISEN since 2018 as SpaceX raised list prices for inflation. No competitor has undercut it.

## Known weaknesses

Published here rather than buried, because a dataset that does not say what it is unsure about is asking to be trusted more than it deserves.

- **New Glenn** — Blue Origin has not published a list price. Reported estimates span $68-110M; the upper bound is used here as the conservative figure.
- **Neutron** — Rocket Lab announced target price ~$50M per launch; vehicle has not flown
- **Ariane 6 (A64)** — EUR 115M per-launch estimate (2018), converted at 1.08 USD/EUR. Arianespace does not publish per-flight pricing.
- **Long March 5** — Estimated ~$160M per launch; Chinese pricing is not publicly listed
- **Saturn V** — Inflation-adjusted per-launch cost; ~$185M nominal 1969, variously adjusted to $1.0-1.5B depending on dollar-year and allocation of development cost
- **Soyuz-2 (Soyuz-ST, Kourou)** — Arianespace commercial Soyuz-ST at Kourou ~$80M; domestic Roscosmos launches reported as low as ~$35M
- **Starship** — Began deploying operational payloads in 2026; no published commercial price

- The frontier series has only 6 anchor points, so any standard error computed from it is close to decorative.
- CPI values for [2025, 2026] are provisional and should be refreshed from BLS once the annual averages are final.
