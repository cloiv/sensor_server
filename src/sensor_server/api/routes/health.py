"""Health check endpoint."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from sensor_server.api.dependencies import get_storage, get_stream_manager

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    storage = get_storage()
    stream_manager = get_stream_manager()

    return JSONResponse({
        "status": "healthy",
        "streaming": stream_manager.is_active,
        "connections": stream_manager.connection_count,
        "arrays_stored": storage.count(),
    })
