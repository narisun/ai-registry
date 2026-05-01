"""Registry's own /health endpoint."""
from __future__ import annotations

from fastapi import APIRouter, Request

health_router = APIRouter()


@health_router.get("/health")
async def health(request: Request):
    store = request.app.state.store
    try:
        await store.list_all()
        db_ok = True
    except Exception:
        db_ok = False
    reaper_ok = getattr(request.app.state, "reaper_task", None) is not None
    status_str = "ok" if (db_ok and reaper_ok) else "degraded"
    return {"status": status_str, "db_ok": db_ok, "reaper_ok": reaper_ok}
