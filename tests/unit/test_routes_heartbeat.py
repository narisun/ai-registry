"""Tests for POST /api/services/{name}/heartbeat."""
from __future__ import annotations

import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def client(tmp_path):
    from src.routes.heartbeat import heartbeat_router
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    asyncio.run(store.init_schema())
    app = FastAPI()
    app.state.store = store
    app.state.api_key = "test-key"
    app.include_router(heartbeat_router)
    return TestClient(app)


def test_heartbeat_requires_auth(client):
    r = client.post("/api/services/x/heartbeat")
    assert r.status_code == 401


def test_heartbeat_404_when_unknown(client):
    r = client.post("/api/services/missing/heartbeat",
                     headers={"Authorization": "Bearer test-key"})
    assert r.status_code == 404


def test_heartbeat_200_when_registered(client, tmp_path):
    from src.store import SqliteStore
    store: SqliteStore = client.app.state.store
    asyncio.run(
        store.register("x", url="http://x", type_="mcp", version=None)
    )
    r = client.post("/api/services/x/heartbeat",
                     headers={"Authorization": "Bearer test-key"})
    assert r.status_code == 200
