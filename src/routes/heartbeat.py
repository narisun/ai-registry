"""POST /api/services/{name}/heartbeat."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from ._auth import require_api_key

heartbeat_router = APIRouter()


@heartbeat_router.post(
    "/api/services/{name}/heartbeat",
    dependencies=[Depends(require_api_key)],
)
async def heartbeat(name: str, request: Request):
    bumped = await request.app.state.store.heartbeat(name)
    if not bumped:
        raise HTTPException(status_code=404, detail=f"Service not registered: {name}")
    return {"ok": True}
