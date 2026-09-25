"""Read-only HTTP API over the dataset.

    uvicorn cost_to_orbit.api:app --reload

Then open http://127.0.0.1:8000/docs.

Auth is optional and off by default, so the repository runs with no setup. Set
COST_TO_ORBIT_API_KEYS to a comma-separated list to require a key:

    COST_TO_ORBIT_API_KEYS=key-one,key-two uvicorn cost_to_orbit.api:app

Keys are read from the environment rather than a checked-in file, because a
credential in version control is a credential that has leaked.
"""

from __future__ import annotations

import os
from collections import defaultdict
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from cost_to_orbit import __version__, analysis
from cost_to_orbit.dataset import load_dataset
from cost_to_orbit.models import Confidence, PriceBasis, Status

DS = load_dataset()

# Optional auth. Empty set means the API is open.
API_KEYS = {k.strip() for k in os.getenv("COST_TO_ORBIT_API_KEYS", "").split(",") if k.strip()}
RATE_LIMIT = int(os.getenv("COST_TO_ORBIT_RATE_LIMIT", "1000"))
_usage: defaultdict[str, int] = defaultdict(int)

DASHBOARD_DIR = Path(__file__).resolve().parents[2] / "dashboard"

app = FastAPI(
    title="Cost-to-Orbit API",
    version=__version__,
    description=(
        "Sourced launch price per kilogram to LEO, with the price basis kept "
        "explicit so statistics are computed within a basis rather than across "
        "them. Read-only."
    ),
)

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"]
)


def require_key(x_api_key: str | None) -> None:
    """No-op when no keys are configured; otherwise validate and count."""
    if not API_KEYS:
        return
    if not x_api_key:
        raise HTTPException(401, "Missing API key. Pass it in the X-API-Key header.")
    if x_api_key not in API_KEYS:
        raise HTTPException(403, "Invalid API key.")
    _usage[x_api_key] += 1
    if _usage[x_api_key] > RATE_LIMIT:
        raise HTTPException(429, f"Request cap ({RATE_LIMIT}) exceeded for this key.")


@app.get("/", tags=["meta"])
def root() -> dict:
    return {
        "service": "Cost-to-Orbit API",
        "version": __version__,
        "last_verified": DS.last_verified,
        "docs": "/docs",
        "auth_required": bool(API_KEYS),
    }


@app.get("/methodology", tags=["meta"])
def methodology() -> dict:
    """How every number is derived. Public on purpose."""
    return {
        "vehicles": DS.methodology,
        "frontier": DS.series_definition,
        "deflator": {
            "series": DS.deflator.series,
            "source": DS.deflator.source,
            "base_year": DS.deflator.base_year,
            "provisional_years": DS.deflator.provisional_years,
        },
    }


@app.get("/vehicles", tags=["data"])
def list_vehicles(
    x_api_key: str | None = Header(default=None),
    basis: PriceBasis | None = Query(default=None, description="Filter by price basis"),
    status: Status | None = Query(default=None),
    country: str | None = Query(default=None, description="Substring match"),
    min_confidence: Confidence | None = Query(default=None),
    priced_only: bool = Query(default=False),
    operational_only: bool = Query(default=False),
) -> dict:
    require_key(x_api_key)
    rows = DS.select(
        basis=basis,
        status=status,
        country=country,
        min_confidence=min_confidence,
        priced_only=priced_only,
        operational_only=operational_only,
    )
    rows = sorted(
        rows, key=lambda v: (v.cost_per_kg_leo is None, v.cost_per_kg_leo or 0)
    )
    return {"count": len(rows), "vehicles": rows}


@app.get("/vehicles/{vehicle_id}", tags=["data"])
def get_vehicle(vehicle_id: str, x_api_key: str | None = Header(default=None)):
    require_key(x_api_key)
    try:
        return DS.get(vehicle_id)
    except KeyError as exc:
        raise HTTPException(404, f"No vehicle with id {vehicle_id!r}") from exc


@app.get("/frontier", tags=["data"])
def frontier(
    x_api_key: str | None = Header(default=None),
    real: bool = Query(default=True, description="Deflate to base-year dollars"),
) -> dict:
    """The frontier decline series, nominal or real."""
    require_key(x_api_key)
    if real:
        points = [
            {
                "year": y,
                "cost_per_kg_leo": round(c),
                "deflator_provisional": prov,
            }
            for y, c, prov in analysis.real_frontier(DS)
        ]
    else:
        points = [
            {"year": p.year, "cost_per_kg_leo": p.cost_per_kg_leo} for p in DS.frontier
        ]
    return {
        "basis": f"real_{DS.deflator.base_year}_usd" if real else "nominal_usd",
        "definition": DS.series_definition,
        "points": points,
        "annotations": [
            {"year": p.year, "vehicle": p.vehicle, "confidence": p.confidence, "note": p.note}
            for p in DS.frontier
        ],
    }


@app.get("/analysis", tags=["analysis"])
def analysis_summary(x_api_key: str | None = Header(default=None)) -> dict:
    """The three findings, computed live from the data."""
    require_key(x_api_key)
    full = analysis.frontier_trend(DS, real=True)
    modern = analysis.frontier_trend(DS, real=True, since=2010)
    return {
        "endpoint_decline_real": analysis.endpoint_decline(DS, real=True),
        "endpoint_decline_nominal": analysis.endpoint_decline(DS, real=False),
        "trend_full_sample": {"summary": full.summary(), "annual_change": full.annual_change},
        "trend_since_2010": {"summary": modern.summary(), "annual_change": modern.annual_change},
        "access_premium": analysis.access_premium(DS),
    }


@app.get("/integrity", tags=["meta"])
def integrity(x_api_key: str | None = Header(default=None)) -> dict:
    """What the dataset does not know. Published rather than buried."""
    require_key(x_api_key)
    return {
        "last_verified": DS.last_verified,
        "unpriced_vehicles": [
            {"id": v.id, "name": v.name, "why": v.source} for v in DS.unpriced()
        ],
        "low_confidence_rows": [
            {"id": v.id, "name": v.name, "why": v.notes} for v in DS.low_confidence()
        ],
        "provisional_deflator_years": DS.deflator.provisional_years,
    }


if DASHBOARD_DIR.exists():
    app.mount("/app", StaticFiles(directory=str(DASHBOARD_DIR), html=True), name="dashboard")
