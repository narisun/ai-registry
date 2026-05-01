"""Tests for reaper — drives state transitions on schedule."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_reaper_one_pass_marks_stale_then_evicts(tmp_path):
    from src.config import RegistryConfig
    from src.config_loader import SeededEntry
    from src.reaper import _run_one_pass
    from src.store import SqliteStore
    import aiosqlite

    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    await store.apply_seed([SeededEntry(name="seeded", type="mcp", expected_url="http://x")])
    await store.register("seeded", url="http://x", type_="mcp", version=None)
    await store.register("unseeded", url="http://y", type_="mcp", version=None)

    # Backdate heartbeats past the grace window
    async with aiosqlite.connect(tmp_path / "r.db") as db:
        old = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
        await db.execute("UPDATE services SET last_heartbeat_at=?", (old,))
        await db.commit()

    config = RegistryConfig(
        port=8090, sqlite_path=tmp_path / "r.db", internal_api_key="k",
        heartbeat_grace_seconds=60, eviction_seconds=300, reaper_interval_seconds=30,
    )
    await _run_one_pass(store, config)
    assert (await store.get("seeded"))["state"] == "stale"
    assert (await store.get("unseeded"))["state"] == "stale"

    # Backdate further (past eviction)
    async with aiosqlite.connect(tmp_path / "r.db") as db:
        old2 = (datetime.now(timezone.utc) - timedelta(seconds=400)).isoformat()
        await db.execute("UPDATE services SET last_heartbeat_at=?", (old2,))
        await db.commit()
    await _run_one_pass(store, config)
    seeded = await store.get("seeded")
    unseeded = await store.get("unseeded")
    assert seeded is not None and seeded["state"] == "expected_unregistered"
    assert unseeded is None
