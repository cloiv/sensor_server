"""WebSocket endpoint for streaming data."""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from sensor_server.api.dependencies import get_stream_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for streaming numpy data to clients.

    Protocol:
    - Client sends: {"action": "start"} to begin streaming
    - Client sends: {"action": "stop"} to stop streaming
    - Client sends: {"action": "ping"} for keep-alive
    - Server sends: {"type": "data", "timestamp": ..., "x": [...], "y": [...]}
    - Server sends: {"type": "status", "streaming": bool}
    - Server sends: {"type": "pong"}
    """
    await websocket.accept()
    stream_manager = get_stream_manager()
    stream_manager.add_connection(websocket)

    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")

            if action == "start":
                await stream_manager.start()
                await websocket.send_json({"type": "status", "streaming": True})
            elif action == "stop":
                await stream_manager.stop()
                await websocket.send_json({"type": "status", "streaming": False})
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        stream_manager.remove_connection(websocket)
        if stream_manager.connection_count == 0:
            await stream_manager.stop()
