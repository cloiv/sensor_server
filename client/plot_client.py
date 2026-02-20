"""
Live plotting client for numpy data streaming.

Uses matplotlib to display real-time data from the WebSocket stream.
"""

import argparse
import asyncio
import json
import threading
from collections import deque
from typing import Deque

import numpy as np
import websockets

try:
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False


class PlotClient:
    """Client that plots streamed numpy data in real-time."""

    def __init__(
        self,
        server_url: str = "http://localhost:8000",
        buffer_size: int = 500
    ):
        self.ws_url = server_url.replace("http", "ws") + "/ws/stream"
        self.buffer_size = buffer_size

        # Data buffers (thread-safe via deque)
        self.x_data: Deque[float] = deque(maxlen=buffer_size)
        self.y_data: Deque[float] = deque(maxlen=buffer_size)
        self.timestamps: Deque[float] = deque(maxlen=buffer_size)

        # State
        self._running = False
        self._connected = False
        self._ws_thread: threading.Thread | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    def start(self) -> None:
        """Start the WebSocket connection in a background thread."""
        self._running = True
        self._ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
        self._ws_thread.start()

    def stop(self) -> None:
        """Stop the WebSocket connection."""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)

    def _run_websocket(self) -> None:
        """Run the WebSocket event loop in a thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._connect_and_stream())
        except Exception as e:
            print(f"WebSocket error: {e}")
        finally:
            self._loop.close()

    async def _connect_and_stream(self) -> None:
        """Connect to WebSocket and receive streaming data."""
        retry_count = 0
        max_retries = 5

        while self._running and retry_count < max_retries:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    self._connected = True
                    retry_count = 0
                    print("Connected to server, starting stream...")

                    # Start streaming
                    await ws.send(json.dumps({"action": "start"}))

                    while self._running:
                        try:
                            message = await asyncio.wait_for(ws.recv(), timeout=1.0)
                            data = json.loads(message)

                            if data.get("type") == "data":
                                self._process_data(data)
                        except asyncio.TimeoutError:
                            continue
                        except websockets.ConnectionClosed:
                            break

            except (ConnectionRefusedError, OSError) as e:
                self._connected = False
                retry_count += 1
                print(f"Connection failed ({retry_count}/{max_retries}): {e}")
                if self._running:
                    await asyncio.sleep(2)

        self._connected = False

    def _process_data(self, data: dict) -> None:
        """Process incoming data packet."""
        x = data.get("x", [])
        y = data.get("y", [])
        timestamp = data.get("timestamp", 0)

        # Add data points to buffers
        for xi, yi in zip(x, y):
            self.x_data.append(xi)
            self.y_data.append(yi)
            self.timestamps.append(timestamp)

    def get_plot_data(self) -> tuple[np.ndarray, np.ndarray]:
        """Get current data for plotting."""
        return np.array(self.x_data), np.array(self.y_data)

    @property
    def is_connected(self) -> bool:
        return self._connected


def run_live_plot(server_url: str = "http://localhost:8000") -> None:
    """Run a live matplotlib plot of streamed data."""
    if not MATPLOTLIB_AVAILABLE:
        print("Error: matplotlib is required for plotting.")
        print("Install with: pip install matplotlib")
        return

    client = PlotClient(server_url)
    client.start()

    # Set up the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
    fig.suptitle("Live Numpy Data Stream")

    # Main signal plot
    line1, = ax1.plot([], [], "b-", linewidth=0.8, label="Signal")
    ax1.set_xlabel("X")
    ax1.set_ylabel("Y")
    ax1.set_title("Streaming Signal")
    ax1.legend(loc="upper right")
    ax1.grid(True, alpha=0.3)

    # Rolling statistics plot
    line2, = ax2.plot([], [], "r-", linewidth=1, label="Rolling Mean")
    line3, = ax2.plot([], [], "g--", linewidth=1, label="Rolling Std")
    ax2.set_xlabel("Sample")
    ax2.set_ylabel("Value")
    ax2.set_title("Rolling Statistics (window=50)")
    ax2.legend(loc="upper right")
    ax2.grid(True, alpha=0.3)

    # Status text
    status_text = ax1.text(
        0.02, 0.95, "",
        transform=ax1.transAxes,
        fontsize=10,
        verticalalignment="top",
        bbox={"boxstyle": "round", "facecolor": "wheat", "alpha": 0.5}
    )

    def init():
        """Initialize animation."""
        line1.set_data([], [])
        line2.set_data([], [])
        line3.set_data([], [])
        return line1, line2, line3, status_text

    def animate(frame):
        """Update animation frame."""
        x, y = client.get_plot_data()

        if len(x) > 0:
            # Update main plot
            line1.set_data(x, y)
            ax1.relim()
            ax1.autoscale_view()

            # Calculate rolling statistics
            window = 50
            if len(y) >= window:
                indices = np.arange(len(y))
                rolling_mean = np.convolve(y, np.ones(window)/window, mode="valid")
                rolling_std = np.array([
                    np.std(y[max(0, i-window):i+1])
                    for i in range(window-1, len(y))
                ])

                line2.set_data(indices[window-1:], rolling_mean)
                line3.set_data(indices[window-1:], rolling_std)
                ax2.relim()
                ax2.autoscale_view()

            # Update status
            status = "Connected" if client.is_connected else "Disconnected"
            status_text.set_text(f"Status: {status}\nPoints: {len(x)}")

        return line1, line2, line3, status_text

    ani = animation.FuncAnimation(
        fig,
        animate,
        init_func=init,
        interval=50,  # 20 FPS
        blit=True,
        cache_frame_data=False
    )

    plt.tight_layout()

    try:
        plt.show()
    finally:
        client.stop()
        print("Plot closed.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Live Plot Client")
    parser.add_argument(
        "--server",
        default="http://localhost:8000",
        help="Server URL (default: http://localhost:8000)"
    )
    args = parser.parse_args()

    print(f"Connecting to {args.server}...")
    print("Close the plot window to exit.")
    run_live_plot(args.server)


if __name__ == "__main__":
    main()
