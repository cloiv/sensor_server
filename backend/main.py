"""
FastAPI backend for numpy data transfer tutorial.

Provides:
- HTTP endpoint for receiving numpy data from clients
- WebSocket endpoint for streaming numpy data to clients
- Control API for start/stop streaming
"""

import asyncio
import io
from typing import Set

import numpy as np
from fastapi import FastAPI, File, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

app = FastAPI(title="Numpy Data Server")

# Store for received numpy arrays (in production, use proper storage)
received_arrays: list[np.ndarray] = []

# Active WebSocket connections for streaming
active_connections: Set[WebSocket] = set()

# Streaming control
streaming_active: bool = False
streaming_task: asyncio.Task | None = None


@app.post("/upload")
async def upload_numpy(file: UploadFile = File(...)) -> JSONResponse:
    """
    Receive a numpy .npy file from the client.

    The file should be saved with np.save() on the client side.
    """
    contents = await file.read()
    buffer = io.BytesIO(contents)

    try:
        array = np.load(buffer, allow_pickle=False)
        received_arrays.append(array)
        return JSONResponse({
            "status": "success",
            "shape": list(array.shape),
            "dtype": str(array.dtype),
            "index": len(received_arrays) - 1
        })
    except Exception as e:
        return JSONResponse(
            {"status": "error", "message": str(e)},
            status_code=400
        )


@app.get("/arrays")
async def list_arrays() -> JSONResponse:
    """List all received numpy arrays with their metadata."""
    return JSONResponse({
        "count": len(received_arrays),
        "arrays": [
            {"index": i, "shape": list(arr.shape), "dtype": str(arr.dtype)}
            for i, arr in enumerate(received_arrays)
        ]
    })


@app.get("/array/{index}")
async def get_array(index: int) -> JSONResponse:
    """Get a specific array by index (returns as nested list for JSON)."""
    if index < 0 or index >= len(received_arrays):
        return JSONResponse(
            {"status": "error", "message": "Array not found"},
            status_code=404
        )

    arr = received_arrays[index]
    return JSONResponse({
        "shape": list(arr.shape),
        "dtype": str(arr.dtype),
        "data": arr.tolist()
    })


@app.websocket("/ws/stream")
async def websocket_stream(websocket: WebSocket) -> None:
    """
    WebSocket endpoint for streaming numpy data to clients.

    Protocol:
    - Client sends: {"action": "start"} to begin streaming
    - Client sends: {"action": "stop"} to stop streaming
    - Server sends: {"type": "data", "shape": [...], "dtype": "...", "data": [...]}
    """
    await websocket.accept()
    active_connections.add(websocket)

    try:
        while True:
            message = await websocket.receive_json()
            action = message.get("action")

            if action == "start":
                await start_streaming()
                await websocket.send_json({"type": "status", "streaming": True})
            elif action == "stop":
                await stop_streaming()
                await websocket.send_json({"type": "status", "streaming": False})
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
    except WebSocketDisconnect:
        active_connections.discard(websocket)
        if not active_connections:
            await stop_streaming()


async def start_streaming() -> None:
    """Start the data streaming task."""
    global streaming_active, streaming_task

    if streaming_active:
        return

    streaming_active = True
    streaming_task = asyncio.create_task(stream_data())


async def stop_streaming() -> None:
    """Stop the data streaming task."""
    global streaming_active, streaming_task

    streaming_active = False
    if streaming_task:
        streaming_task.cancel()
        try:
            await streaming_task
        except asyncio.CancelledError:
            pass
        streaming_task = None


async def stream_data() -> None:
    """
    Generate and stream dummy numpy data to all connected clients.

    In production, this would stream real sensor data.
    """
    t = 0.0

    while streaming_active:
        # Generate dummy sine wave data (simulating sensor readings)
        x = np.linspace(t, t + 2 * np.pi, 100)
        y = np.sin(x) + 0.1 * np.random.randn(100)

        data_packet = {
            "type": "data",
            "timestamp": t,
            "shape": [100],
            "dtype": "float64",
            "x": x.tolist(),
            "y": y.tolist()
        }

        # Broadcast to all connected clients
        disconnected = set()
        for ws in active_connections:
            try:
                await ws.send_json(data_packet)
            except Exception:
                disconnected.add(ws)

        active_connections.difference_update(disconnected)

        t += 0.1
        await asyncio.sleep(0.05)  # ~20 FPS


@app.post("/control/start")
async def control_start() -> JSONResponse:
    """HTTP endpoint to start streaming (alternative to WebSocket control)."""
    await start_streaming()
    return JSONResponse({"status": "streaming started"})


@app.post("/control/stop")
async def control_stop() -> JSONResponse:
    """HTTP endpoint to stop streaming (alternative to WebSocket control)."""
    await stop_streaming()
    return JSONResponse({"status": "streaming stopped"})


@app.get("/health")
async def health() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "streaming": streaming_active,
        "connections": len(active_connections),
        "arrays_stored": len(received_arrays)
    })


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
