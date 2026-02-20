"""Pytest configuration and fixtures."""

import io
from typing import Generator

import numpy as np
import pytest
from fastapi.testclient import TestClient

from sensor_server.api.app import create_app
from sensor_server.api.dependencies import reset_state


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client and clean up state after each test."""
    reset_state()
    app = create_app()

    with TestClient(app) as test_client:
        yield test_client

    reset_state()


@pytest.fixture
def sample_array() -> np.ndarray:
    """Create a sample numpy array for testing."""
    return np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]], dtype=np.float64)


@pytest.fixture
def sample_npy_bytes(sample_array: np.ndarray) -> bytes:
    """Convert sample array to .npy bytes."""
    buffer = io.BytesIO()
    np.save(buffer, sample_array)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def large_array() -> np.ndarray:
    """Create a larger array for performance testing."""
    return np.random.randn(1000, 100).astype(np.float32)
