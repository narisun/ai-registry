"""GET / — serve the read-only HTML catalog."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

ui_router = APIRouter()
_INDEX = Path(__file__).parent.parent / "ui" / "index.html"


@ui_router.get("/", response_class=HTMLResponse)
async def index():
    return _INDEX.read_text()
