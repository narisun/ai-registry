"""Reaper background task — drives state transitions on schedule."""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta

from .config import RegistryConfig
from .store import SqliteStore


async def _run_one_pass(store: SqliteStore, config: RegistryConfig) -> None:
    now = datetime.now(timezone.utc)
    stale_cutoff = (now - timedelta(seconds=config.heartbeat_grace_seconds)).isoformat()
    for name in await store.find_stale_candidates(older_than_iso=stale_cutoff):
        await store.mark_stale(name)
    evict_cutoff = (now - timedelta(seconds=config.eviction_seconds)).isoformat()
    for name in await store.find_eviction_candidates(older_than_iso=evict_cutoff):
        await store.evict(name)


async def reaper_loop(store: SqliteStore, config: RegistryConfig) -> None:
    """Forever loop. Cancel the asyncio.Task to stop."""
    while True:
        try:
            await _run_one_pass(store, config)
        except asyncio.CancelledError:
            raise
        except Exception:
            from platform_sdk.logging import get_logger
            get_logger("ai-registry").warning("reaper_pass_failed", exc_info=True)
        await asyncio.sleep(config.reaper_interval_seconds)
