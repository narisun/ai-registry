"""Tests for SqliteStore — schema, CRUD, idempotent apply_seed, reaper queries."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

import pytest

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_init_schema_creates_db(tmp_path):
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    assert (tmp_path / "r.db").exists()


@pytest.mark.asyncio
async def test_register_then_get(tmp_path):
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    await store.register("ai-mcp-data", url="http://data-mcp:8080", type_="mcp", version="0.5.0")
    row = await store.get("ai-mcp-data")
    assert row["state"] == "registered"
    assert row["url"] == "http://data-mcp:8080"


@pytest.mark.asyncio
async def test_register_is_upsert(tmp_path):
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    await store.register("x", url="http://x:1", type_="mcp", version="1")
    await store.register("x", url="http://x:2", type_="mcp", version="2")
    row = await store.get("x")
    assert row["url"] == "http://x:2" and row["version"] == "2"


@pytest.mark.asyncio
async def test_heartbeat_bumps_timestamp(tmp_path):
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    await store.register("x", url="http://x", type_="mcp", version=None)
    pre = (await store.get("x"))["last_heartbeat_at"]
    await asyncio.sleep(0.05)
    await store.heartbeat("x")
    post = (await store.get("x"))["last_heartbeat_at"]
    assert post > pre


@pytest.mark.asyncio
async def test_heartbeat_returns_false_when_unknown(tmp_path):
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    assert (await store.heartbeat("missing")) is False


@pytest.mark.asyncio
async def test_deregister_unseeded_deletes(tmp_path):
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    await store.register("x", url="http://x", type_="mcp", version=None)
    await store.deregister("x")
    assert (await store.get("x")) is None


@pytest.mark.asyncio
async def test_deregister_seeded_returns_to_expected_unregistered(tmp_path):
    from src.store import SqliteStore
    from src.config_loader import SeededEntry
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    await store.apply_seed([SeededEntry(name="x", type="mcp", expected_url="http://x:8080")])
    await store.register("x", url="http://x:8080", type_="mcp", version=None)
    await store.deregister("x")
    assert (await store.get("x"))["state"] == "expected_unregistered"


@pytest.mark.asyncio
async def test_apply_seed_is_idempotent(tmp_path):
    from src.store import SqliteStore
    from src.config_loader import SeededEntry
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    seed = [SeededEntry(name="a", type="mcp", expected_url="http://a"),
            SeededEntry(name="b", type="agent", expected_url="http://b")]
    await store.apply_seed(seed)
    await store.apply_seed(seed)
    assert len(await store.list_all()) == 2


@pytest.mark.asyncio
async def test_reaper_query_helpers(tmp_path):
    from src.store import SqliteStore
    store = SqliteStore(tmp_path / "r.db")
    await store.init_schema()
    await store.register("x", url="http://x", type_="mcp", version=None)
    # Backdate
    import aiosqlite
    async with aiosqlite.connect(tmp_path / "r.db") as db:
        old = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
        await db.execute("UPDATE services SET last_heartbeat_at=?", (old,))
        await db.commit()
    cutoff = (datetime.now(timezone.utc) - timedelta(seconds=60)).isoformat()
    candidates = await store.find_stale_candidates(older_than_iso=cutoff)
    assert "x" in candidates
