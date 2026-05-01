"""Tests for the read endpoints (no auth required)."""
from __future__ import annotations

import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def client(tmp_path):
    from src.routes.lookup import lookup_router
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    asyncio.run(store.init_schema())
    asyncio.run(
        store.register("ai-mcp-data", url="http://data-mcp:8080", type_="mcp", version="0.5.0")
    )
    app = FastAPI()
    app.state.store = store
    app.include_router(lookup_router)
    return TestClient(app)


def test_get_services_returns_list(client):
    r = client.get("/api/services")
    assert r.status_code == 200
    assert "services" in r.json()
    names = [s["name"] for s in r.json()["services"]]
    assert "ai-mcp-data" in names


def test_get_service_by_name_returns_entry(client):
    r = client.get("/api/services/ai-mcp-data")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "ai-mcp-data"
    assert body["state"] == "registered"


def test_get_unknown_returns_404(client):
    r = client.get("/api/services/missing")
    assert r.status_code == 404


def test_read_endpoints_unauthenticated(client):
    """Read endpoints do not require Authorization."""
    r = client.get("/api/services")
    assert r.status_code == 200
