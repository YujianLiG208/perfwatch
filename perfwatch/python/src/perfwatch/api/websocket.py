from __future__ import annotations

import asyncio

from fastapi import APIRouter, WebSocket

from perfwatch.collectors.native import get_snapshot

router = APIRouter()


@router.websocket("/ws/snapshot")
async def snapshot_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    while True:
        await websocket.send_json(get_snapshot())
        await asyncio.sleep(1.0)
