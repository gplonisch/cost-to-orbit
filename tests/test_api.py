"""API behaviour, including the auth path, which is off by default."""

import importlib

import pytest
from fastapi.testclient import TestClient

from cost_to_orbit import api


@pytest.fixture
def client():
    return TestClient(api.app)


def test_root_reports_open_auth_by_default(client):
    body = client.get("/").json()
    assert body["auth_required"] is False
    assert "last_verified" in body


def test_methodology_is_public(client):
    body = client.get("/methodology").json()
    assert "price_basis_values" in body["vehicles"]
    assert body["deflator"]["base_year"] == 2026


def test_vehicles_sorted_cheapest_first_with_unpriced_last(client):
    rows = client.get("/vehicles").json()["vehicles"]
    costs = [r["cost_per_kg_leo"] for r in rows]
    priced = [c for c in costs if c is not None]
    assert priced == sorted(priced)
    assert costs[-1] is None  # Starship


def test_basis_filter(client):
    rows = client.get("/vehicles", params={"basis": "program_cost"}).json()["vehicles"]
    assert {r["id"] for r in rows} == {"space-shuttle", "saturn-v"}


def test_unknown_vehicle_is_404(client):
    assert client.get("/vehicles/does-not-exist").status_code == 404


def test_frontier_real_differs_from_nominal(client):
    real = client.get("/frontier", params={"real": True}).json()
    nominal = client.get("/frontier", params={"real": False}).json()
    assert real["basis"] == "real_2026_usd"
    assert real["points"][0]["cost_per_kg_leo"] != nominal["points"][0]["cost_per_kg_leo"]


def test_analysis_endpoint_returns_all_three_findings(client):
    body = client.get("/analysis").json()
    assert body["endpoint_decline_real"]["decline_factor"] > 0
    assert "fell" in body["trend_since_2010"]["summary"]
    assert body["access_premium"]["premium_vs_frontier"] > 1


def test_integrity_publishes_what_is_missing(client):
    body = client.get("/integrity").json()
    assert any(v["id"] == "starship" for v in body["unpriced_vehicles"])
    assert body["provisional_deflator_years"] == [2025, 2026]


def test_auth_is_enforced_when_keys_are_configured(monkeypatch):
    monkeypatch.setenv("COST_TO_ORBIT_API_KEYS", "secret-key")
    importlib.reload(api)
    guarded = TestClient(api.app)
    try:
        assert guarded.get("/vehicles").status_code == 401
        assert guarded.get("/vehicles", headers={"X-API-Key": "wrong"}).status_code == 403
        assert guarded.get("/vehicles", headers={"X-API-Key": "secret-key"}).status_code == 200
        assert guarded.get("/methodology").status_code == 200  # meta stays public
    finally:
        monkeypatch.delenv("COST_TO_ORBIT_API_KEYS")
        importlib.reload(api)
