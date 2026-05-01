"""Tests for RegistryConfig — fail-fast validation, env loading."""
import pytest

pytestmark = pytest.mark.unit


def test_defaults_construct(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_KEY", "test")
    for k in ("REGISTRY_PORT", "SQLITE_PATH", "SEED_PATH",
              "HEARTBEAT_GRACE_SECONDS", "EVICTION_SECONDS",
              "REAPER_INTERVAL_SECONDS"):
        monkeypatch.delenv(k, raising=False)
    from src.config import RegistryConfig
    cfg = RegistryConfig.from_env()
    assert cfg.port == 8090
    assert cfg.heartbeat_grace_seconds == 60
    assert cfg.eviction_seconds == 300
    assert cfg.reaper_interval_seconds == 30


def test_validation_rejects_negative_grace():
    from src.config import RegistryConfig
    with pytest.raises(ValueError, match="heartbeat_grace_seconds"):
        RegistryConfig(
            port=8090, sqlite_path="/tmp/x.db", internal_api_key="k",
            heartbeat_grace_seconds=-1, eviction_seconds=300, reaper_interval_seconds=30,
        )


def test_validation_lists_all_errors_at_once():
    from src.config import RegistryConfig
    with pytest.raises(ValueError) as exc:
        RegistryConfig(
            port=-1, sqlite_path="/tmp/x.db", internal_api_key="",
            heartbeat_grace_seconds=10, eviction_seconds=5,  # eviction < grace = invalid
            reaper_interval_seconds=30,
        )
    msg = str(exc.value)
    assert "port" in msg
    assert "internal_api_key" in msg
    assert "eviction_seconds" in msg
