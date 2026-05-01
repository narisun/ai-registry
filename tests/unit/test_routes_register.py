"""Tests for the register/deregister routes."""
from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def client(tmp_path):
    from src.routes.register import register_router
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    asyncio.run(store.init_schema())
    app = FastAPI()
    app.state.store = store
    app.state.api_key = "test-key"
    app.include_router(register_router)
    return TestClient(app)


def test_post_services_requires_auth(client):
    r = client.post("/api/services", json={
        "name": "x", "url": "http://x", "type": "mcp",
    })
    assert r.status_code == 401


def test_post_services_creates_entry(client):
    r = client.post(
        "/api/services",
        headers={"Authorization": "Bearer test-key"},
        json={"name": "ai-mcp-data", "url": "http://data-mcp:8080", "type": "mcp"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "ai-mcp-data"
    assert body["state"] == "registered"


def test_post_services_idempotent_on_repeat(client):
    headers = {"Authorization": "Bearer test-key"}
    body = {"name": "x", "url": "http://x:1", "type": "mcp"}
    r1 = client.post("/api/services", headers=headers, json=body)
    r2 = client.post("/api/services", headers=headers, json={**body, "url": "http://x:2"})
    assert r1.status_code == 200
    assert r2.status_code == 200
    # Re-registration with new URL should win
    assert r2.json()["url"].rstrip("/") == "http://x:2"


def test_delete_services_removes_or_unregisters(client):
    headers = {"Authorization": "Bearer test-key"}
    client.post("/api/services", headers=headers, json={
        "name": "x", "url": "http://x", "type": "mcp",
    })
    r = client.delete("/api/services/x", headers=headers)
    assert r.status_code == 204
