from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from perfwatch.api.routes import router as routes_router
from perfwatch.api.service import ServiceState
from perfwatch.api.websocket import router as websocket_router
from perfwatch.collectors import Collector, create_collector
from perfwatch.config.settings import Settings, get_settings
from perfwatch.storage.sqlite_writer import SQLiteWriter


def create_app(
    *,
    settings: Settings | None = None,
    collector: Collector | None = None,
    repository: SQLiteWriter | None = None,
    dashboard_directory: Path | None = None,
) -> FastAPI:
    resolved_settings = settings or get_settings()
    service = ServiceState(
        settings=resolved_settings,
        collector=collector
        or create_collector(use_mock=resolved_settings.use_mock_collector),
        repository=repository or SQLiteWriter(resolved_settings.database_path),
    )

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        application.state.service = service
        await service.start()
        try:
            yield
        finally:
            await service.stop()

    application = FastAPI(title="perfwatch", version="0.1.0", lifespan=lifespan)
    application.state.service = service
    application.include_router(routes_router)
    application.include_router(websocket_router)
    if dashboard_directory is not None:
        application.mount(
            "/",
            StaticFiles(directory=dashboard_directory, html=True),
            name="dashboard",
        )
    return application


app = create_app()
