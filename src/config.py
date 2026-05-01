"""RegistryConfig — typed config with fail-fast validation."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RegistryConfig:
    port: int = 8090
    sqlite_path: Path = field(default_factory=lambda: Path("/var/lib/registry/registry.db"))
    seed_path: Path | None = None
    internal_api_key: str = ""
    heartbeat_grace_seconds: int = 60
    eviction_seconds: int = 300
    reaper_interval_seconds: int = 30
    service_url: str = ""
    enable_ui: bool = True

    def __post_init__(self) -> None:
        errors: list[str] = []
        if self.port <= 0 or self.port > 65535:
            errors.append(f"port={self.port} must be in 1..65535")
        if not self.internal_api_key:
            errors.append("internal_api_key must not be empty (set INTERNAL_API_KEY env)")
        if self.heartbeat_grace_seconds < 0:
            errors.append(f"heartbeat_grace_seconds={self.heartbeat_grace_seconds} cannot be negative")
        if self.eviction_seconds < self.heartbeat_grace_seconds:
            errors.append(
                f"eviction_seconds={self.eviction_seconds} must be >= "
                f"heartbeat_grace_seconds={self.heartbeat_grace_seconds}"
            )
        if self.reaper_interval_seconds <= 0:
            errors.append(f"reaper_interval_seconds={self.reaper_interval_seconds} must be positive")
        if isinstance(self.sqlite_path, str):
            self.sqlite_path = Path(self.sqlite_path)
        if self.seed_path is not None and isinstance(self.seed_path, str):
            self.seed_path = Path(self.seed_path)
        if errors:
            raise ValueError(f"RegistryConfig validation failed: {'; '.join(errors)}")

    @classmethod
    def from_env(cls) -> "RegistryConfig":
        seed = os.environ.get("SEED_PATH", "")
        return cls(
            port=int(os.environ.get("REGISTRY_PORT", "8090")),
            sqlite_path=Path(os.environ.get("SQLITE_PATH", "/var/lib/registry/registry.db")),
            seed_path=Path(seed) if seed else None,
            internal_api_key=os.environ.get("INTERNAL_API_KEY", ""),
            heartbeat_grace_seconds=int(os.environ.get("HEARTBEAT_GRACE_SECONDS", "60")),
            eviction_seconds=int(os.environ.get("EVICTION_SECONDS", "300")),
            reaper_interval_seconds=int(os.environ.get("REAPER_INTERVAL_SECONDS", "30")),
            service_url=os.environ.get("SERVICE_URL", ""),
            enable_ui=os.environ.get("ENABLE_UI", "true").lower() != "false",
        )
