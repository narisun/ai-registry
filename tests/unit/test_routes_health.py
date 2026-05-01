"""Tests for GET /health."""
from __future__ import annotations

import asyncio
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_health_reports_db_reachable(tmp_path):
    from src.routes.health import health_router
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    asyncio.run(store.init_schema())
    app = FastAPI()
    app.state.store = store
    app.include_router(health_router)
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] in ("ok", "degraded")
    assert "db_ok" in body
