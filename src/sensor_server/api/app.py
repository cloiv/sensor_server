"""FastAPI application factory."""

from fastapi import FastAPI

from sensor_server.api.routes import health_router, arrays_router, control_router
from sensor_server.api.websocket import router as websocket_router


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="Numpy Data Server",
        description="FastAPI backend for numpy data transfer",
        version="0.1.0",
    )

    # Include routers
    app.include_router(health_router)
    app.include_router(arrays_router)
    app.include_router(control_router)
    app.include_router(websocket_router)

    return app


# Default app instance for uvicorn
app = create_app()
