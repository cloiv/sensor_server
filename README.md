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
├── src/
│   └── sensor_server/           # Installable Python package
│       ├── __init__.py
│       ├── cli.py               # CLI entry point
│       ├── core/                # Pure business logic (no HTTP)
│       │   ├── __init__.py
│       │   ├── processing.py    # Numpy operations
│       │   ├── streaming.py     # Data generation
│       │   └── storage.py       # Array storage
│       └── api/                 # FastAPI layer
│           ├── __init__.py
│           ├── app.py           # App factory
│           ├── dependencies.py  # Shared state
│           ├── websocket.py     # WebSocket handler
│           └── routes/
│               ├── __init__.py
│               ├── arrays.py    # /upload, /arrays, /array/{id}
│               ├── control.py   # /control/start, /control/stop
│               └── health.py    # /health
├── client/
│   ├── client.py                # Python client
│   └── plot_client.py           # Live plotting client
├── tests/
│   ├── conftest.py
│   ├── unit/                    # Tests for core/ modules
│   │   ├── test_processing.py
│   │   ├── test_storage.py
│   │   └── test_streaming.py
│   └── integration/             # Tests for api/ endpoints
│       ├── test_http_endpoints.py
│       └── test_websocket.py
├── pyproject.toml
├── Dockerfile
└── README.md
```

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone https://github.com/cloiv/sensor_server.git
cd sensor_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install in development mode with all dependencies
pip install -e ".[dev,client]"
```

### Server Only

```bash
pip install -e .
```

## Running the Server

```bash
# Using the CLI
sensor-server run

# With custom host/port
sensor-server run --host 0.0.0.0 --port 8080

# With auto-reload for development
sensor-server run --reload

# Using uvicorn directly
uvicorn sensor_server.api.app:app --host 0.0.0.0 --port 8000 --reload
```

The server will be available at `http://localhost:8000`.

## Running Tests

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run only unit tests (fast, no HTTP)
pytest tests/unit/

# Run only integration tests
pytest tests/integration/

# Run with coverage
pip install pytest-cov
pytest --cov=sensor_server --cov-report=term-missing
```

### Test Coverage

The test suite includes:

- **Unit Tests** (core modules, no HTTP overhead)
  - `test_storage.py` - ArrayStorage class
  - `test_streaming.py` - DataFrame and DataStreamer
  - `test_processing.py` - Numpy serialization utilities

- **Integration Tests** (API endpoints)
  - `test_http_endpoints.py` - Upload, list, get arrays, control
  - `test_websocket.py` - WebSocket streaming

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

```bash
# Start the live plot (requires matplotlib)
python client/plot_client.py

# Connect to a different server
python client/plot_client.py --server http://192.168.1.100:8000
```

### Programmatic Usage

```python
from client.client import NumpyClient
import numpy as np

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

client.close()
```

### Using Core Modules Directly

The `core` modules have no HTTP dependencies and can be used standalone:

```python
from sensor_server.core import ArrayStorage, DataStreamer, load_array_from_bytes

# Use storage directly
storage = ArrayStorage()
storage.add(np.array([1, 2, 3]))
print(storage.list_all())

# Generate streaming data without a server
streamer = DataStreamer(sample_rate=0.1, points_per_frame=50)
for _ in range(10):
    frame = streamer.generate_frame()
    print(f"t={frame.timestamp:.1f}, mean={frame.y.mean():.3f}")
```

## Docker Deployment

```bash
# Build the image
docker build -t sensor-server .

# Run the container
docker run -p 8000:8000 sensor-server

# Run in detached mode
docker run -d -p 8000:8000 --name sensor-server sensor-server

# Check logs
docker logs -f sensor-server

# Stop the container
docker stop sensor-server
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

## Package Architecture

The package separates concerns into two layers:

| Layer | Location | Dependencies | HTTP-aware? |
|-------|----------|--------------|-------------|
| Core | `sensor_server/core/` | numpy, stdlib | No |
| API | `sensor_server/api/` | FastAPI, core | Yes |

This separation allows:
- Importing `core` modules without running a server
- Fast unit tests with no HTTP overhead
- Swapping the API layer (e.g., gRPC) without touching business logic
- Using core modules in CLI tools, Jupyter notebooks, or other services

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
