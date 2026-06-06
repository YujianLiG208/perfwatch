from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query, Request

from perfwatch.api.service import ServiceState

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/snapshot")
def snapshot(request: Request) -> dict[str, Any]:
    service = _get_service(request)
    if service.current_snapshot is None:
        raise HTTPException(status_code=503, detail="snapshot unavailable")
    return service.current_snapshot


@router.get("/metrics/recent")
def recent_metrics(
    request: Request,
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[dict[str, Any]]:
    return _get_service(request).repository.get_recent_metrics(limit=limit)


@router.get("/processes/top")
def top_processes(
    request: Request,
    limit: int = Query(default=10, ge=1, le=100),
) -> list[dict[str, Any]]:
    service = _get_service(request)
    timestamp_ms = (
        int(service.current_snapshot["timestamp_ms"])
        if service.current_snapshot is not None
        else None
    )
    return service.repository.get_top_processes(
        limit=limit,
        timestamp_ms=timestamp_ms,
    )


def _get_service(request: Request) -> ServiceState:
    return request.app.state.service
