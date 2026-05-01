"""SqliteStore — single-table catalog (aiosqlite)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import aiosqlite

from .config_loader import SeededEntry

_DDL = """
CREATE TABLE IF NOT EXISTS services (
    name              TEXT PRIMARY KEY,
    url               TEXT,
    expected_url      TEXT,
    type              TEXT NOT NULL,
    state             TEXT NOT NULL,
    version           TEXT,
    metadata_json     TEXT,
    last_heartbeat_at TEXT,
    registered_at     TEXT,
    last_changed_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    environment       TEXT NOT NULL DEFAULT 'dev'
);
CREATE INDEX IF NOT EXISTS idx_services_state ON services (state);
CREATE INDEX IF NOT EXISTS idx_services_type  ON services (type);
"""

_MIGRATE_ADD_ENVIRONMENT = (
    "ALTER TABLE services ADD COLUMN environment TEXT NOT NULL DEFAULT 'dev'"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_to_dict(row: aiosqlite.Row) -> dict[str, Any]:
    out = dict(row)
    out["metadata"] = json.loads(out.pop("metadata_json") or "{}")
    return out


class SqliteStore:
    def __init__(self, path: Path) -> None:
        self.path = Path(path)

    def _conn(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        return aiosqlite.connect(self.path)

    async def init_schema(self) -> None:
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            await db.executescript(_DDL)
            # Non-destructive migration: add environment column to existing databases.
            try:
                await db.execute(_MIGRATE_ADD_ENVIRONMENT)
            except Exception:
                pass  # Column already exists (OperationalError) — safe to ignore.
            await db.commit()

    async def apply_seed(self, seed: Iterable[SeededEntry]) -> None:
        rows = [(s.name, s.expected_url, s.type, "expected_unregistered",
                 json.dumps(s.metadata), _now()) for s in seed]
        if not rows:
            return
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            await db.executemany(
                "INSERT OR IGNORE INTO services "
                "(name, expected_url, type, state, metadata_json, last_changed_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                rows,
            )
            await db.commit()

    async def register(self, name: str, *, url: str, type_: str,
                       version: str | None, metadata: dict | None = None,
                       environment: str = "dev") -> None:
        now = _now()
        meta_json = json.dumps(metadata or {})
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            await db.execute(
                """
                INSERT INTO services (
                    name, url, type, state, version, metadata_json,
                    registered_at, last_heartbeat_at, last_changed_at, environment
                ) VALUES (?, ?, ?, 'registered', ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    url=excluded.url,
                    type=excluded.type,
                    state='registered',
                    version=excluded.version,
                    metadata_json=excluded.metadata_json,
                    registered_at=COALESCE(services.registered_at, ?),
                    last_heartbeat_at=?,
                    last_changed_at=?,
                    environment=excluded.environment
                """,
                (name, url, type_, version, meta_json, now, now, now, environment, now, now, now),
            )
            await db.commit()

    async def heartbeat(self, name: str) -> bool:
        now = _now()
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "UPDATE services SET last_heartbeat_at=?, state='registered', last_changed_at=? "
                "WHERE name=? AND state IN ('registered', 'stale')",
                (now, now, name),
            )
            await db.commit()
            return cur.rowcount > 0

    async def deregister(self, name: str) -> None:
        now = _now()
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT expected_url FROM services WHERE name=?", (name,))
            row = await cur.fetchone()
            if row is None:
                return
            if row["expected_url"]:
                await db.execute(
                    "UPDATE services SET state='expected_unregistered', "
                    "url=NULL, last_heartbeat_at=NULL, last_changed_at=? WHERE name=?",
                    (now, name),
                )
            else:
                await db.execute("DELETE FROM services WHERE name=?", (name,))
            await db.commit()

    async def mark_stale(self, name: str) -> None:
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            await db.execute(
                "UPDATE services SET state='stale', last_changed_at=? WHERE name=?",
                (_now(), name),
            )
            await db.commit()

    async def evict(self, name: str) -> None:
        await self.deregister(name)

    async def get(self, name: str) -> dict | None:
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM services WHERE name=?", (name,))
            row = await cur.fetchone()
            return _row_to_dict(row) if row else None

    async def list_all(self) -> list[dict]:
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute("SELECT * FROM services ORDER BY name")
            rows = await cur.fetchall()
            return [_row_to_dict(r) for r in rows]

    async def list_by_env(self, environment: str) -> list[dict]:
        """Return only entries whose environment matches the given value."""
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM services WHERE environment=? ORDER BY name",
                (environment,),
            )
            rows = await cur.fetchall()
            return [_row_to_dict(r) for r in rows]

    async def get_in_env(self, name: str, environment: str) -> dict | None:
        """Return the named entry only if it belongs to the given environment."""
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT * FROM services WHERE name=? AND environment=?",
                (name, environment),
            )
            row = await cur.fetchone()
            return _row_to_dict(row) if row else None

    async def find_stale_candidates(self, *, older_than_iso: str) -> list[str]:
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT name FROM services WHERE state='registered' "
                "AND (last_heartbeat_at IS NULL OR last_heartbeat_at < ?)",
                (older_than_iso,),
            )
            return [r["name"] for r in await cur.fetchall()]

    async def find_eviction_candidates(self, *, older_than_iso: str) -> list[str]:
        async with self._conn() as db:
            db.row_factory = aiosqlite.Row
            cur = await db.execute(
                "SELECT name FROM services WHERE state='stale' "
                "AND (last_heartbeat_at IS NULL OR last_heartbeat_at < ?)",
                (older_than_iso,),
            )
            return [r["name"] for r in await cur.fetchall()]
