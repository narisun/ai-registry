"""POST /api/services and DELETE /api/services/{name}."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from platform_sdk.registry import RegistrationRequest

from ._auth import require_api_key

register_router = APIRouter()


@register_router.post("/api/services", dependencies=[Depends(require_api_key)])
async def register(request: Request, body: RegistrationRequest):
    store = request.app.state.store
    client_env = request.headers.get("X-Environment", "")
    await store.register(
        body.name, url=str(body.url), type_=body.type,
        version=body.version, metadata=body.metadata,
        environment=client_env,
    )
    row = await store.get(body.name)
    return row


@register_router.delete(
    "/api/services/{name}",
    dependencies=[Depends(require_api_key)],
    status_code=status.HTTP_204_NO_CONTENT,
)
async def deregister(name: str, request: Request):
    await request.app.state.store.deregister(name)
    return Response(status_code=204)
