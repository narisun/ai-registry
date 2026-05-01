"""GET /api/services and /api/services/{name} — unauthenticated reads."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

lookup_router = APIRouter()


@lookup_router.get("/api/services")
async def list_services(request: Request):
    rows = await request.app.state.store.list_all()
    return {"services": rows}


@lookup_router.get("/api/services/{name}")
async def get_service(name: str, request: Request):
    row = await request.app.state.store.get(name)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Service not found: {name}")
    return row
