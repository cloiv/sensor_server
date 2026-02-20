"""
Tests for HTTP endpoints in the backend.
"""

import io

import numpy as np
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_check_returns_ok(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "healthy"
        assert "streaming" in data
        assert "connections" in data
        assert "arrays_stored" in data

    def test_health_shows_zero_arrays_initially(self, client: TestClient) -> None:
        response = client.get("/health")
        assert response.json()["arrays_stored"] == 0


class TestUploadEndpoint:
    """Tests for the /upload endpoint."""

    def test_upload_valid_npy_file(
        self, client: TestClient, sample_npy_bytes: bytes
    ) -> None:
        response = client.post(
            "/upload",
            files={"file": ("test.npy", sample_npy_bytes, "application/octet-stream")}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["shape"] == [2, 3]
        assert data["dtype"] == "float64"
        assert data["index"] == 0

    def test_upload_multiple_arrays(
        self, client: TestClient, sample_npy_bytes: bytes
    ) -> None:
        # Upload first array
        response1 = client.post(
            "/upload",
            files={"file": ("test1.npy", sample_npy_bytes, "application/octet-stream")}
        )
        assert response1.json()["index"] == 0

        # Upload second array
        response2 = client.post(
            "/upload",
            files={"file": ("test2.npy", sample_npy_bytes, "application/octet-stream")}
        )
        assert response2.json()["index"] == 1

    def test_upload_invalid_file_returns_error(self, client: TestClient) -> None:
        response = client.post(
            "/upload",
            files={"file": ("test.npy", b"not a valid npy file", "application/octet-stream")}
        )
        assert response.status_code == 400
        assert response.json()["status"] == "error"

    def test_upload_different_dtypes(self, client: TestClient) -> None:
        dtypes = [np.float32, np.float64, np.int32, np.int64]

        for i, dtype in enumerate(dtypes):
            array = np.array([1, 2, 3], dtype=dtype)
            buffer = io.BytesIO()
            np.save(buffer, array)
            buffer.seek(0)

            response = client.post(
                "/upload",
                files={"file": (f"test_{dtype}.npy", buffer.read(), "application/octet-stream")}
            )
            assert response.status_code == 200
            assert response.json()["dtype"] == str(dtype().dtype)
            assert response.json()["index"] == i

    def test_upload_large_array(
        self, client: TestClient, large_array: np.ndarray
    ) -> None:
        buffer = io.BytesIO()
        np.save(buffer, large_array)
        buffer.seek(0)

        response = client.post(
            "/upload",
            files={"file": ("large.npy", buffer.read(), "application/octet-stream")}
        )
        assert response.status_code == 200
        assert response.json()["shape"] == [1000, 100]


class TestArraysEndpoint:
    """Tests for the /arrays endpoint."""

    def test_list_arrays_empty(self, client: TestClient) -> None:
        response = client.get("/arrays")
        assert response.status_code == 200

        data = response.json()
        assert data["count"] == 0
        assert data["arrays"] == []

    def test_list_arrays_after_upload(
        self, client: TestClient, sample_npy_bytes: bytes
    ) -> None:
        # Upload an array
        client.post(
            "/upload",
            files={"file": ("test.npy", sample_npy_bytes, "application/octet-stream")}
        )

        response = client.get("/arrays")
        data = response.json()

        assert data["count"] == 1
        assert len(data["arrays"]) == 1
        assert data["arrays"][0]["index"] == 0
        assert data["arrays"][0]["shape"] == [2, 3]


class TestGetArrayEndpoint:
    """Tests for the /array/{index} endpoint."""

    def test_get_array_not_found(self, client: TestClient) -> None:
        response = client.get("/array/0")
        assert response.status_code == 404
        assert response.json()["status"] == "error"

    def test_get_array_negative_index(self, client: TestClient) -> None:
        response = client.get("/array/-1")
        assert response.status_code == 404

    def test_get_array_after_upload(
        self, client: TestClient, sample_array: np.ndarray, sample_npy_bytes: bytes
    ) -> None:
        # Upload the array
        client.post(
            "/upload",
            files={"file": ("test.npy", sample_npy_bytes, "application/octet-stream")}
        )

        response = client.get("/array/0")
        assert response.status_code == 200

        data = response.json()
        assert data["shape"] == [2, 3]
        assert data["dtype"] == "float64"

        # Verify data matches
        retrieved = np.array(data["data"], dtype=data["dtype"])
        np.testing.assert_array_equal(retrieved, sample_array)


class TestControlEndpoints:
    """Tests for the /control/* endpoints."""

    def test_start_streaming(self, client: TestClient) -> None:
        response = client.post("/control/start")
        assert response.status_code == 200
        assert "started" in response.json()["status"]

    def test_stop_streaming(self, client: TestClient) -> None:
        response = client.post("/control/stop")
        assert response.status_code == 200
        assert "stopped" in response.json()["status"]

    def test_start_stop_sequence(self, client: TestClient) -> None:
        # Start
        start_response = client.post("/control/start")
        assert start_response.status_code == 200

        # Verify streaming state via health
        health = client.get("/health").json()
        assert health["streaming"] is True

        # Stop
        stop_response = client.post("/control/stop")
        assert stop_response.status_code == 200

        # Verify stopped
        health = client.get("/health").json()
        assert health["streaming"] is False
