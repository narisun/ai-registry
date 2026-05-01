"""Tests for RegistryConfig — Pydantic validation."""
import pytest

pytestmark = pytest.mark.unit


def test_defaults_construct():
    from src.config import RegistryConfig
    cfg = RegistryConfig(environment="dev", internal_api_key="test")
    assert cfg.port == 8090
    assert cfg.heartbeat_grace_seconds == 60
    assert cfg.eviction_seconds == 300
    assert cfg.reaper_interval_seconds == 30


def test_validation_rejects_negative_grace():
    from src.config import RegistryConfig
    with pytest.raises(Exception, match="heartbeat_grace_seconds"):
        RegistryConfig(
            environment="dev",
            port=8090, sqlite_path="/tmp/x.db", internal_api_key="k",
            heartbeat_grace_seconds=-1, eviction_seconds=300, reaper_interval_seconds=30,
        )


def test_validation_lists_all_errors_at_once():
    from src.config import RegistryConfig
    with pytest.raises(Exception) as exc:
        RegistryConfig(
            environment="dev",
            port=-1, sqlite_path="/tmp/x.db", internal_api_key="",
            heartbeat_grace_seconds=10, eviction_seconds=5,  # eviction < grace = invalid
            reaper_interval_seconds=30,
        )
    msg = str(exc.value)
    assert "port" in msg
    assert "internal_api_key" in msg
    assert "eviction_seconds" in msg
