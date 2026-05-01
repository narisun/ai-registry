"""ConfigLoader — parses optional registry.yaml seed."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class SeededEntry:
    name: str
    type: str
    expected_url: str
    metadata: dict[str, Any] = field(default_factory=dict)


class ConfigLoader:
    def __init__(self, seed_path: Path | None) -> None:
        self.seed_path = seed_path

    def load(self) -> list[SeededEntry]:
        if self.seed_path is None or not self.seed_path.exists():
            return []
        try:
            data = yaml.safe_load(self.seed_path.read_text()) or {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Failed to parse {self.seed_path}: {exc}") from exc

        services_raw = data.get("services", []) or []
        if not isinstance(services_raw, list):
            raise ValueError(f"{self.seed_path}: 'services' must be a list")

        entries: list[SeededEntry] = []
        errors: list[str] = []
        for i, raw in enumerate(services_raw):
            if not isinstance(raw, dict):
                errors.append(f"[{i}] entry must be a mapping")
                continue
            entry_errors: list[str] = []
            for required in ("name", "type", "expected_url"):
                if required not in raw:
                    entry_errors.append(f"[{i}] missing required field: {required}")
            if entry_errors:
                errors.extend(entry_errors)
                continue
            entries.append(SeededEntry(
                name=raw["name"], type=raw["type"],
                expected_url=raw["expected_url"],
                metadata=raw.get("metadata", {}) or {},
            ))
        if errors:
            raise ValueError(f"Seed validation failed: {'; '.join(errors)}")
        return entries
