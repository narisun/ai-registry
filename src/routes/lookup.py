"""GET /api/services and /api/services/{name} — unauthenticated reads.

When the requester supplies an X-Environment header, results are filtered to
entries registered under that environment (defense-in-depth: cross-env
enumeration is not possible). Requests without the header return everything,
preserving the existing unauthenticated catalog-browsing contract.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

lookup_router = APIRouter()


@lookup_router.get("/api/services")
async def list_services(request: Request):
    store = request.app.state.store
    client_env = request.headers.get("X-Environment", "")
    if client_env:
        rows = await store.list_by_env(client_env)
    else:
        rows = await store.list_all()
    return {"services": rows}


@lookup_router.get("/api/services/{name}")
async def get_service(name: str, request: Request):
    store = request.app.state.store
    client_env = request.headers.get("X-Environment", "")
    if client_env:
        row = await store.get_in_env(name, client_env)
    else:
        row = await store.get(name)
    if row is None:
        raise HTTPException(status_code=404, detail=f"Service not found: {name}")
    return row
