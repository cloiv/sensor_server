# FastAPI + Uvicorn Numpy Data Transfer Tutorial

This tutorial demonstrates how to build a Python backend using FastAPI + uvicorn to receive and send numpy data, with support for real-time streaming.

## Architecture

```
Client A ──HTTP/WS──> Host B ──> Container C (FastAPI Server)
```

Or when client and host are the same:

```
Client = Host B ──HTTP/WS──> Container C (FastAPI Server)
```

## Project Structure

```
sensor_server/
├── backend/
│   └── main.py              # FastAPI server
├── client/
│   ├── client.py            # Python client
│   └── plot_client.py       # Live plotting client
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_http_endpoints.py
│   └── test_websocket.py
├── Dockerfile
├── pytest.ini
├── requirements.txt
└── README.md
```

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_http_endpoints.py

# Run specific test class
pytest tests/test_websocket.py::TestWebSocketConnection

# Run with coverage (requires pytest-cov)
pip install pytest-cov
pytest --cov=backend --cov-report=term-missing
```

### Test Coverage

The test suite covers:

- **HTTP Endpoints** (15 tests)
  - Health check endpoint
  - Numpy file upload (valid/invalid files, multiple dtypes)
  - Array listing and retrieval
  - Streaming control endpoints

- **WebSocket Streaming** (9 tests)
  - Connection handling
  - Start/stop streaming
  - Data packet format validation
  - Multiple concurrent clients

## Running the Server

```bash
# Option 1: Direct run
python backend/main.py

# Option 2: Using uvicorn directly (recommended for development)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at `http://localhost:8000`.

## API Endpoints

### HTTP Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/upload` | POST | Upload a numpy `.npy` file |
| `/arrays` | GET | List all stored arrays |
| `/array/{index}` | GET | Get array by index (as JSON) |
| `/control/start` | POST | Start data streaming |
| `/control/stop` | POST | Stop data streaming |
| `/health` | GET | Health check |

### WebSocket Endpoint

| Endpoint | Description |
|----------|-------------|
| `/ws/stream` | Real-time numpy data streaming |

## Using the Client

### Command Line Interface

```bash
# Check server health
python client/client.py health

# Upload a demo array
python client/client.py upload-demo

# Upload a numpy file
python client/client.py upload path/to/your/array.npy

# List all stored arrays
python client/client.py list

# Get a specific array
python client/client.py get 0

# Start streaming demo (receives data for 5 seconds)
python client/client.py stream --duration 5
```

### Live Plotting

The plot client provides real-time visualization of streamed data:

```bash
# Start the live plot (requires matplotlib)
python client/plot_client.py

# Connect to a different server
python client/plot_client.py --server http://192.168.1.100:8000
```

The plot window shows:
- **Top panel**: Live streaming signal (sine wave + noise)
- **Bottom panel**: Rolling mean and standard deviation

Close the plot window to disconnect.

### Programmatic Usage

```python
from client.client import NumpyClient
import numpy as np
import asyncio

# Create client
client = NumpyClient("http://localhost:8000")

# Upload a numpy array
array = np.random.randn(100, 50)
result = client.upload_numpy_array(array)
print(f"Uploaded: {result}")

# List arrays
print(client.list_arrays())

# Download an array
downloaded = client.get_array(0)
print(f"Downloaded shape: {downloaded.shape}")

# Streaming with custom callback
def handle_data(data):
    x = np.array(data["x"])
    y = np.array(data["y"])
    print(f"Received: {len(x)} points, mean={y.mean():.3f}")

async def stream_demo():
    await client.connect_streaming(on_data=handle_data, auto_start=True)

# Run streaming for a few seconds
asyncio.run(stream_demo())

client.close()
```

## How It Works

### Uploading Numpy Data

1. Client saves numpy array to bytes using `np.save()`
2. Sends as multipart file upload to `/upload`
3. Server reads bytes with `np.load()` and stores the array

```python
# Client side
buffer = io.BytesIO()
np.save(buffer, array)
buffer.seek(0)
# Send buffer as file upload

# Server side
contents = await file.read()
buffer = io.BytesIO(contents)
array = np.load(buffer, allow_pickle=False)
```

### Streaming Numpy Data

1. Client connects to WebSocket at `/ws/stream`
2. Sends `{"action": "start"}` to begin streaming
3. Server generates data and broadcasts to all connected clients
4. Client sends `{"action": "stop"}` to stop streaming

```python
# Server generates data
x = np.linspace(t, t + 2 * np.pi, 100)
y = np.sin(x) + noise

# Sends as JSON
await ws.send_json({
    "type": "data",
    "timestamp": t,
    "x": x.tolist(),
    "y": y.tolist()
})
```

## Docker Deployment

A `Dockerfile` is included in the project:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for numpy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir \
    fastapi>=0.100.0 \
    "uvicorn[standard]>=0.23.0" \
    numpy>=1.24.0 \
    python-multipart>=0.0.6

# Copy backend code
COPY backend/ ./backend/

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```bash
# Build the image
docker build -t numpy-server .

# Run the container
docker run -p 8000:8000 numpy-server

# Run in detached mode
docker run -d -p 8000:8000 --name numpy-server numpy-server

# Check logs
docker logs -f numpy-server

# Stop the container
docker stop numpy-server
```

### Connecting from Client to Container

```bash
# If container is on the same host
python client/client.py --server http://localhost:8000 health

# If container is on a different host
python client/client.py --server http://<container-host-ip>:8000 health

# Live plotting to container
python client/plot_client.py --server http://<container-host-ip>:8000
```

## Protocol Details

### WebSocket Message Format

**Client to Server:**
```json
{"action": "start"}   // Start streaming
{"action": "stop"}    // Stop streaming
{"action": "ping"}    // Keep-alive ping
```

**Server to Client:**
```json
{
    "type": "data",
    "timestamp": 0.0,
    "shape": [100],
    "dtype": "float64",
    "x": [...],
    "y": [...]
}
```

```json
{"type": "status", "streaming": true}
{"type": "pong"}
```

### Upload Response Format

```json
{
    "status": "success",
    "shape": [100, 50],
    "dtype": "float64",
    "index": 0
}
```

## Notes

- The streaming demo generates sine wave data with noise to simulate sensor readings
- In production, replace the `stream_data()` function with actual sensor data
- The server supports multiple concurrent WebSocket clients
- Use HTTP control endpoints (`/control/start`, `/control/stop`) when you need to control streaming from non-WebSocket clients (e.g., curl, other services)
