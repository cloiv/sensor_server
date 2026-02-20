"""
Tests for WebSocket streaming endpoint.
"""

import pytest
from fastapi.testclient import TestClient


class TestWebSocketConnection:
    """Tests for WebSocket connection handling."""

    def test_websocket_connect(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as websocket:
            # Send ping to verify connection
            websocket.send_json({"action": "ping"})
            response = websocket.receive_json()
            assert response["type"] == "pong"

    def test_websocket_start_streaming(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as websocket:
            websocket.send_json({"action": "start"})
            response = websocket.receive_json()

            assert response["type"] == "status"
            assert response["streaming"] is True

    def test_websocket_stop_streaming(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as websocket:
            # Start first
            websocket.send_json({"action": "start"})
            websocket.receive_json()

            # Then stop
            websocket.send_json({"action": "stop"})

            # May receive data packets before status, so drain until we get status
            for _ in range(10):
                response = websocket.receive_json()
                if response["type"] == "status":
                    break

            assert response["type"] == "status"
            assert response["streaming"] is False

    def test_websocket_receives_data_after_start(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as websocket:
            websocket.send_json({"action": "start"})
            # Skip status message
            websocket.receive_json()

            # Receive data packet
            data = websocket.receive_json()

            assert data["type"] == "data"
            assert "timestamp" in data
            assert "x" in data
            assert "y" in data
            assert data["shape"] == [100]
            assert data["dtype"] == "float64"

    def test_websocket_data_has_correct_format(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as websocket:
            websocket.send_json({"action": "start"})
            websocket.receive_json()  # Skip status

            data = websocket.receive_json()

            # Check data arrays have correct length
            assert len(data["x"]) == 100
            assert len(data["y"]) == 100

            # Check values are numeric
            assert all(isinstance(v, (int, float)) for v in data["x"])
            assert all(isinstance(v, (int, float)) for v in data["y"])

    def test_websocket_multiple_data_packets(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as websocket:
            websocket.send_json({"action": "start"})
            websocket.receive_json()  # Skip status

            timestamps = []
            for _ in range(3):
                data = websocket.receive_json()
                timestamps.append(data["timestamp"])

            # Timestamps should be increasing
            assert timestamps[1] > timestamps[0]
            assert timestamps[2] > timestamps[1]

    def test_websocket_stop_halts_data(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as websocket:
            # Start streaming
            websocket.send_json({"action": "start"})
            websocket.receive_json()

            # Receive a few packets
            for _ in range(2):
                websocket.receive_json()

            # Stop streaming
            websocket.send_json({"action": "stop"})

            # Drain any pending data packets until we get the status
            for _ in range(10):
                stop_response = websocket.receive_json()
                if stop_response["type"] == "status":
                    break

            assert stop_response["type"] == "status"
            assert stop_response["streaming"] is False


class TestMultipleClients:
    """Tests for multiple WebSocket clients."""

    def test_two_clients_receive_data(self, client: TestClient) -> None:
        with client.websocket_connect("/ws/stream") as ws1:
            with client.websocket_connect("/ws/stream") as ws2:
                # Start streaming from first client
                ws1.send_json({"action": "start"})
                ws1.receive_json()  # Status for ws1

                # Both clients should receive data
                data1 = ws1.receive_json()
                data2 = ws2.receive_json()

                assert data1["type"] == "data"
                assert data2["type"] == "data"

    def test_health_shows_connection_count(self, client: TestClient) -> None:
        # Initially no connections
        health = client.get("/health").json()
        assert health["connections"] == 0

        with client.websocket_connect("/ws/stream"):
            health = client.get("/health").json()
            assert health["connections"] == 1

            with client.websocket_connect("/ws/stream"):
                health = client.get("/health").json()
                assert health["connections"] == 2

        # After disconnect
        health = client.get("/health").json()
        assert health["connections"] == 0
