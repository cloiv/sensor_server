"""API route modules."""

from sensor_server.api.routes.health import router as health_router
from sensor_server.api.routes.arrays import router as arrays_router
from sensor_server.api.routes.control import router as control_router

__all__ = ["health_router", "arrays_router", "control_router"]
