"""ai-registry — service catalog + health-aware lookup.

Subclasses BaseAgentApp so we get the same lifecycle wiring (logging, telemetry,
graceful shutdown, optional auto-registration). RegistryApp does NOT register
itself with itself — Application._register checks REGISTRY_URL == SERVICE_URL
and skips.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass

from platform_sdk import BaseAgentApp

from .config import RegistryConfig
from .config_loader import ConfigLoader
from .reaper import reaper_loop
from .routes.health import health_router
from .routes.heartbeat import heartbeat_router
from .routes.lookup import lookup_router
from .routes.register import register_router
from .routes.ui import ui_router
from .store import SqliteStore


@dataclass
class RegistryDeps:
    store: SqliteStore
    config: RegistryConfig


class RegistryApp(BaseAgentApp):
    service_name = "ai-registry"
    service_title = "ai-registry"
    service_description = "Enterprise AI Platform — service catalog, health, discovery"
    service_type = "registry"
    enable_telemetry = True
    requires_checkpointer = False
    requires_conversation_store = False

    config_model = RegistryConfig

    def routes(self):
        # Order: UI router last so /api/* take precedence (defensive — FastAPI matches
        # by route definition not order, but consistent ordering helps readers).
        return [register_router, heartbeat_router, lookup_router, health_router, ui_router]

    def build_dependencies(self, *, bridges, checkpointer, store):
        cfg: RegistryConfig = self.config
        return RegistryDeps(store=SqliteStore(cfg.sqlite_path), config=cfg)

    async def on_started(self, deps: RegistryDeps, *, bridges, config, checkpointer, store):
        # Make config / store available to route handlers via app.state
        from fastapi import FastAPI
        app: FastAPI = self._app  # set in create_app override below

        await deps.store.init_schema()
        seed = ConfigLoader(seed_path=deps.config.seed_path).load()
        await deps.store.apply_seed(seed)

        app.state.store = deps.store
        app.state.api_key = deps.config.internal_api_key
        app.state.environment = deps.config.environment
        app.state.reaper_task = asyncio.create_task(reaper_loop(deps.store, deps.config))

    async def on_shutdown(self, deps: RegistryDeps):
        from fastapi import FastAPI
        app: FastAPI = self._app
        task = getattr(app.state, "reaper_task", None)
        if task is not None:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            app.state.reaper_task = None

    def create_app(self, deps=None):
        # Capture the FastAPI instance so on_started can write to app.state
        app = super().create_app(deps=deps)
        self._app = app
        return app


import os as _os

def _make_app():
    """Create the WSGI app, loading config from the environment.

    Deferred to a function so that test code that imports *only* RegistryApp
    (and supplies an explicit config=) is not forced to have ENVIRONMENT set
    at import time.
    """
    _r = RegistryApp()
    return _r.create_app()


# Only auto-construct when the module is loaded as the uvicorn entry-point
# (i.e. ENVIRONMENT is already set in the process).  Tests that want the full
# app can call _make_app() with the required env vars in place.
if _os.environ.get("ENVIRONMENT"):
    _registry = RegistryApp()
    app = _registry.create_app()
else:
    # Stub — replaced by test fixtures or uvicorn once ENVIRONMENT is set.
    app = None  # type: ignore[assignment]
