"""
Dummy client for numpy data transfer tutorial.

Provides:
- Upload numpy files to the backend
- Receive streaming numpy data via WebSocket
- Control streaming (start/stop)
- Simple live plotting of received data
"""

import argparse
import asyncio
import io
import json
import sys
from pathlib import Path
from typing import Callable

import httpx
import numpy as np
import websockets


class NumpyClient:
    """Client for interacting with the numpy data server."""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.ws_url = base_url.replace("http", "ws") + "/ws/stream"
        self.http_client = httpx.Client(timeout=30.0)
        self.websocket: websockets.WebSocketClientProtocol | None = None
        self._streaming = False

    def upload_numpy_file(self, filepath: str | Path) -> dict:
        """
        Upload a numpy .npy file to the server.

        Args:
            filepath: Path to the .npy file

        Returns:
            Server response with array metadata
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        if not filepath.suffix == ".npy":
            raise ValueError("File must be a .npy file")

        with open(filepath, "rb") as f:
            files = {"file": (filepath.name, f, "application/octet-stream")}
            response = self.http_client.post(f"{self.base_url}/upload", files=files)

        return response.json()

    def upload_numpy_array(self, array: np.ndarray, name: str = "array.npy") -> dict:
        """
        Upload a numpy array directly to the server.

        Args:
            array: Numpy array to upload
            name: Filename to use

        Returns:
            Server response with array metadata
        """
        buffer = io.BytesIO()
        np.save(buffer, array)
        buffer.seek(0)

        files = {"file": (name, buffer, "application/octet-stream")}
        response = self.http_client.post(f"{self.base_url}/upload", files=files)
        return response.json()

    def list_arrays(self) -> dict:
        """Get list of all arrays stored on the server."""
        response = self.http_client.get(f"{self.base_url}/arrays")
        return response.json()

    def get_array(self, index: int) -> np.ndarray:
        """
        Download an array from the server.

        Args:
            index: Array index on the server

        Returns:
            Numpy array
        """
        response = self.http_client.get(f"{self.base_url}/array/{index}")
        data = response.json()

        if "error" in data.get("status", ""):
            raise ValueError(data.get("message", "Unknown error"))

        return np.array(data["data"], dtype=data["dtype"])

    def health_check(self) -> dict:
        """Check server health status."""
        response = self.http_client.get(f"{self.base_url}/health")
        return response.json()

    def start_streaming_http(self) -> dict:
        """Start streaming via HTTP control endpoint."""
        response = self.http_client.post(f"{self.base_url}/control/start")
        return response.json()

    def stop_streaming_http(self) -> dict:
        """Stop streaming via HTTP control endpoint."""
        response = self.http_client.post(f"{self.base_url}/control/stop")
        return response.json()

    async def connect_streaming(
        self,
        on_data: Callable[[dict], None] | None = None,
        auto_start: bool = True
    ) -> None:
        """
        Connect to WebSocket and receive streaming data.

        Args:
            on_data: Callback function for each data packet
            auto_start: Whether to start streaming immediately
        """
        async with websockets.connect(self.ws_url) as ws:
            self.websocket = ws
            self._streaming = True

            if auto_start:
                await ws.send(json.dumps({"action": "start"}))

            try:
                async for message in ws:
                    data = json.loads(message)

                    if data.get("type") == "data" and on_data:
                        on_data(data)
                    elif data.get("type") == "status":
                        print(f"Streaming status: {data.get('streaming')}")
                    elif data.get("type") == "pong":
                        print("Pong received")

                    if not self._streaming:
                        break
            finally:
                self._streaming = False
                self.websocket = None

    async def start_streaming(self) -> None:
        """Send start streaming command via WebSocket."""
        if self.websocket:
            await self.websocket.send(json.dumps({"action": "start"}))

    async def stop_streaming(self) -> None:
        """Send stop streaming command via WebSocket."""
        if self.websocket:
            await self.websocket.send(json.dumps({"action": "stop"}))

    def disconnect(self) -> None:
        """Disconnect from streaming."""
        self._streaming = False

    def close(self) -> None:
        """Close HTTP client."""
        self.http_client.close()


def print_data_callback(data: dict) -> None:
    """Simple callback that prints received data info."""
    timestamp = data.get("timestamp", 0)
    shape = data.get("shape", [])
    print(f"Received data: timestamp={timestamp:.2f}, shape={shape}")


async def demo_streaming(client: NumpyClient, duration: float = 5.0) -> None:
    """Demo streaming for a specified duration."""
    received_count = 0

    def count_callback(data: dict) -> None:
        nonlocal received_count
        received_count += 1
        if received_count % 20 == 0:
            print(f"Received {received_count} data packets...")

    print(f"Starting streaming demo for {duration} seconds...")

    async def run_stream() -> None:
        await client.connect_streaming(on_data=count_callback, auto_start=True)

    stream_task = asyncio.create_task(run_stream())

    await asyncio.sleep(duration)
    client.disconnect()

    try:
        await asyncio.wait_for(stream_task, timeout=1.0)
    except asyncio.TimeoutError:
        pass

    print(f"Streaming demo complete. Received {received_count} packets.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Numpy Data Client")
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Upload command
    upload_parser = subparsers.add_parser("upload", help="Upload a numpy file")
    upload_parser.add_argument("file", help="Path to .npy file")

    # Upload demo command
    subparsers.add_parser("upload-demo", help="Upload a demo numpy array")

    # List command
    subparsers.add_parser("list", help="List stored arrays")

    # Get command
    get_parser = subparsers.add_parser("get", help="Get an array by index")
    get_parser.add_argument("index", type=int, help="Array index")

    # Stream command
    stream_parser = subparsers.add_parser("stream", help="Start streaming demo")
    stream_parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Duration in seconds (default: 5.0)"
    )

    # Health command
    subparsers.add_parser("health", help="Check server health")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    client = NumpyClient(args.server)

    try:
        if args.command == "upload":
            result = client.upload_numpy_file(args.file)
            print(f"Upload result: {json.dumps(result, indent=2)}")

        elif args.command == "upload-demo":
            demo_array = np.random.randn(100, 100).astype(np.float32)
            result = client.upload_numpy_array(demo_array, "demo.npy")
            print(f"Uploaded demo array (100x100 random): {json.dumps(result, indent=2)}")

        elif args.command == "list":
            result = client.list_arrays()
            print(f"Stored arrays: {json.dumps(result, indent=2)}")

        elif args.command == "get":
            array = client.get_array(args.index)
            print(f"Retrieved array: shape={array.shape}, dtype={array.dtype}")
            print(f"First few values: {array.flat[:5]}")

        elif args.command == "stream":
            asyncio.run(demo_streaming(client, args.duration))

        elif args.command == "health":
            result = client.health_check()
            print(f"Server health: {json.dumps(result, indent=2)}")

    finally:
        client.close()


if __name__ == "__main__":
    main()
