from __future__ import annotations

from fastapi import FastAPI

from perfwatch.api.routes import router as routes_router
from perfwatch.api.websocket import router as websocket_router

app = FastAPI(title="perfwatch", version="0.1.0")
app.include_router(routes_router)
app.include_router(websocket_router)
