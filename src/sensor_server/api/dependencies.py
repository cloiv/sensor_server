"""Shared dependencies and state for the API layer."""

import asyncio
from typing import Set

from fastapi import WebSocket

from sensor_server.core.storage import ArrayStorage
from sensor_server.core.streaming import DataStreamer

# Global instances (in production, use proper dependency injection)
_storage: ArrayStorage | None = None
_stream_manager: "StreamManager | None" = None


def get_storage() -> ArrayStorage:
    """Get the global array storage instance."""
    global _storage
    if _storage is None:
        _storage = ArrayStorage()
    return _storage


def get_stream_manager() -> "StreamManager":
    """Get the global stream manager instance."""
    global _stream_manager
    if _stream_manager is None:
        _stream_manager = StreamManager()
    return _stream_manager


def reset_state() -> None:
    """Reset global state (for testing)."""
    global _storage, _stream_manager
    if _storage is not None:
        _storage.clear()
    if _stream_manager is not None:
        _stream_manager.connections.clear()
    _storage = None
    _stream_manager = None


class StreamManager:
    """Manages WebSocket connections and data streaming."""

    def __init__(self) -> None:
        self.connections: Set[WebSocket] = set()
        self.streamer = DataStreamer()
        self._active = False
        self._task: asyncio.Task | None = None

    @property
    def is_active(self) -> bool:
        """Whether streaming is currently active."""
        return self._active

    @property
    def connection_count(self) -> int:
        """Number of active WebSocket connections."""
        return len(self.connections)

    def add_connection(self, websocket: WebSocket) -> None:
        """Register a new WebSocket connection."""
        self.connections.add(websocket)

    def remove_connection(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        self.connections.discard(websocket)

    async def start(self) -> None:
        """Start streaming data to all connections."""
        if self._active:
            return

        self._active = True
        self._task = asyncio.create_task(self._stream_loop())

    async def stop(self) -> None:
        """Stop streaming data."""
        self._active = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def _stream_loop(self) -> None:
        """Main streaming loop - generates and broadcasts data."""
        while self._active:
            frame = self.streamer.generate_frame()
            data = frame.to_dict()

            # Broadcast to all connections
            disconnected = set()
            for ws in self.connections:
                try:
                    await ws.send_json(data)
                except Exception:
                    disconnected.add(ws)

            self.connections.difference_update(disconnected)

            await asyncio.sleep(self.streamer.sample_rate)
