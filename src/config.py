"""Registry server configuration (Pydantic v2)."""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator

from platform_sdk.config.env_isolation import Environment


class RegistryConfig(BaseModel):
    """Configuration for the registry server."""

    model_config = ConfigDict(extra="forbid")

    environment: Environment

    # Server runtime
    port: Annotated[int, Field(gt=0, le=65535)] = 8090

    # Storage
    sqlite_path: Path = Path("/var/lib/registry/registry.db")
    seed_path: Path | None = None

    # Auth
    internal_api_key: str

    # Reaper
    heartbeat_grace_seconds: Annotated[int, Field(ge=0)] = 60
    eviction_seconds: int = 300
    reaper_interval_seconds: Annotated[int, Field(gt=0)] = 30

    # Self-URL (rarely used; registry usually doesn't register itself)
    service_url: str = ""
    registry_url: str = ""
    service_version: str = ""

    # UI
    enable_ui: bool = True

    @field_validator("internal_api_key")
    @classmethod
    def _require_api_key(cls, v: str) -> str:
        if not v:
            raise ValueError(
                "internal_api_key must not be empty (set INTERNAL_API_KEY env)"
            )
        return v

    @field_validator("eviction_seconds")
    @classmethod
    def _validate_eviction_vs_grace(cls, v, info):
        grace = info.data.get("heartbeat_grace_seconds", 0)
        if v < grace:
            raise ValueError(
                f"eviction_seconds={v} must be >= heartbeat_grace_seconds={grace}"
            )
        return v

    @classmethod
    def load(cls, *, config_dir: str | None = None, env: str | None = None) -> "RegistryConfig":
        from platform_sdk.config.loader import load_config
        return load_config(cls, config_dir=config_dir, env=env)
