from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from perfwatch.api.service import ServiceState

router = APIRouter()


@router.websocket("/ws/snapshot")
async def snapshot_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    service: ServiceState = websocket.app.state.service

    try:
        while True:
            if service.current_snapshot is not None:
                await websocket.send_json(service.current_snapshot)
            await asyncio.sleep(service.settings.snapshot_interval_seconds)
    except WebSocketDisconnect:
        return
