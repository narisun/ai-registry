"""Component-level smoke test — full RegistryApp lifecycle in-process."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.component


@pytest.fixture
def app(tmp_path):
    from src.config import RegistryConfig
    from src.app import RegistryApp

    cfg = RegistryConfig(
        environment="dev",
        internal_api_key="test-key",
        sqlite_path=tmp_path / "r.db",
        seed_path=None,
    )
    registry = RegistryApp(config=cfg)
    return registry.create_app()


def test_full_register_heartbeat_lookup_deregister(app):
    with TestClient(app) as client:
        headers = {"Authorization": "Bearer test-key", "X-Environment": "dev"}

        # 1. List is empty (no seed)
        r = client.get("/api/services")
        assert r.status_code == 200
        assert r.json()["services"] == []

        # 2. Register
        r = client.post("/api/services", headers=headers, json={
            "name": "ai-mcp-data", "url": "http://data-mcp:8080", "type": "mcp",
        })
        assert r.status_code == 200

        # 3. Lookup
        r = client.get("/api/services/ai-mcp-data")
        assert r.status_code == 200
        assert r.json()["state"] == "registered"

        # 4. Heartbeat
        r = client.post("/api/services/ai-mcp-data/heartbeat", headers=headers)
        assert r.status_code == 200

        # 5. Health
        r = client.get("/health")
        assert r.status_code == 200
        body = r.json()
        assert body["db_ok"] is True

        # 6. UI returns HTML
        r = client.get("/")
        assert r.status_code == 200
        assert "ai-registry" in r.text

        # 7. Deregister
        r = client.delete("/api/services/ai-mcp-data", headers=headers)
        assert r.status_code == 204

        r = client.get("/api/services/ai-mcp-data")
        assert r.status_code == 404
