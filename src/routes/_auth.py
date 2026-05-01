"""Bearer-token guard. Reads the expected key off app.state.api_key (set in lifespan)."""
from __future__ import annotations

from fastapi import HTTPException, Request, status


async def require_api_key(request: Request) -> None:
    expected = getattr(request.app.state, "api_key", None)
    auth = request.headers.get("authorization", "")
    if not expected or not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    token = auth.split(" ", 1)[1]
    if token != expected:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
