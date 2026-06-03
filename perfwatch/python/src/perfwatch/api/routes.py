from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from perfwatch.collectors.native import get_snapshot

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/snapshot")
def snapshot() -> dict[str, Any]:
    return get_snapshot()
