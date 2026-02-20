"""Streaming control endpoints."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from sensor_server.api.dependencies import get_stream_manager

router = APIRouter(prefix="/control", tags=["control"])


@router.post("/start")
async def control_start() -> JSONResponse:
    """Start streaming via HTTP endpoint."""
    stream_manager = get_stream_manager()
    await stream_manager.start()
    return JSONResponse({"status": "streaming started"})


@router.post("/stop")
async def control_stop() -> JSONResponse:
    """Stop streaming via HTTP endpoint."""
    stream_manager = get_stream_manager()
    await stream_manager.stop()
    return JSONResponse({"status": "streaming stopped"})
