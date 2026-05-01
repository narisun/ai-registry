"""Per-entry environment stamping and lookup filtering."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


@pytest.fixture
def client(tmp_path):
    from src.config import RegistryConfig
    from src.app import RegistryApp

    cfg = RegistryConfig(
        environment="dev",
        internal_api_key="test-key",
        sqlite_path=tmp_path / "test.db",
    )
    app_inst = RegistryApp(config=cfg)
    fastapi_app = app_inst.create_app()
    with TestClient(fastapi_app) as c:
        yield c


def _register(client, name, env):
    return client.post(
        "/api/services",
        json={"name": name, "url": f"http://{name}/", "type": "agent"},
        headers={"Authorization": "Bearer test-key", "X-Environment": env},
    )


def test_register_stamps_environment_from_header(client):
    r = _register(client, "alice", "dev")
    assert r.status_code in (200, 201)

    # Read back via lookup with same env header.
    listing = client.get("/api/services", headers={"X-Environment": "dev"})
    services = listing.json().get("services", [])
    found = next((s for s in services if s["name"] == "alice"), None)
    assert found is not None
    assert found.get("environment") == "dev"


def test_lookup_with_x_environment_filters_results(client):
    # Register one in dev (this works — auth dep passes).
    _register(client, "alice", "dev")

    # A lookup with X-Environment: prod sees no entries (defense-in-depth filter).
    listing = client.get("/api/services", headers={"X-Environment": "prod"})
    services = listing.json().get("services", [])
    assert all(s.get("environment") != "dev" for s in services), \
        "dev-stamped entries leaked to a prod lookup"


def test_lookup_without_x_environment_sees_all(client):
    _register(client, "alice", "dev")

    listing = client.get("/api/services")
    services = listing.json().get("services", [])
    assert any(s["name"] == "alice" for s in services), \
        "unauthenticated lookup should still return all entries"


def test_lookup_by_name_404_for_cross_env(client):
    _register(client, "alice", "dev")

    r = client.get("/api/services/alice", headers={"X-Environment": "prod"})
    assert r.status_code == 404, \
        "named lookup should hide cross-env entries (returns 404, not the entry)"
