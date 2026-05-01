"""Bearer-token + X-Environment guard. Reads expected values from app.state (set in lifespan)."""
from __future__ import annotations

from fastapi import HTTPException, Request, status

from platform_sdk.config.env_isolation import ENV_HEADER


async def require_api_key(request: Request) -> None:
    """Validate Bearer auth and X-Environment header against the registry's own config."""
    expected_key = getattr(request.app.state, "api_key", None)
    expected_env = getattr(request.app.state, "environment", None)

    auth = request.headers.get("authorization", "")
    if not expected_key or not auth.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Missing or invalid Authorization header")
    token = auth.split(" ", 1)[1]
    if token != expected_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")

    # L2 environment isolation: the registry rejects writes from any env that
    # doesn't match its own.
    if expected_env is not None:
        got = request.headers.get(ENV_HEADER)
        if got != expected_env:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": "environment_mismatch",
                    "expected": expected_env,
                    "got": got or "",
                },
            )
