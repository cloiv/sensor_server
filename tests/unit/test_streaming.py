"""Unit tests for core.streaming module."""

import numpy as np

from sensor_server.core.streaming import DataFrame, DataStreamer


class TestDataFrame:
    """Tests for DataFrame class."""

    def test_create_dataframe(self) -> None:
        x = np.array([1.0, 2.0, 3.0])
        y = np.array([4.0, 5.0, 6.0])
        frame = DataFrame(timestamp=0.5, x=x, y=y)

        assert frame.timestamp == 0.5
        np.testing.assert_array_equal(frame.x, x)
        np.testing.assert_array_equal(frame.y, y)

    def test_to_dict(self) -> None:
        x = np.array([1.0, 2.0])
        y = np.array([3.0, 4.0])
        frame = DataFrame(timestamp=1.0, x=x, y=y)

        result = frame.to_dict()

        assert result["type"] == "data"
        assert result["timestamp"] == 1.0
        assert result["shape"] == [2]
        assert result["dtype"] == "float64"
        assert result["x"] == [1.0, 2.0]
        assert result["y"] == [3.0, 4.0]


class TestDataStreamer:
    """Tests for DataStreamer class."""

    def test_default_config(self) -> None:
        streamer = DataStreamer()

        assert streamer.sample_rate == 0.05
        assert streamer.points_per_frame == 100
        assert streamer.noise_level == 0.1
        assert streamer.time == 0.0

    def test_custom_config(self) -> None:
        streamer = DataStreamer(
            sample_rate=0.1,
            points_per_frame=50,
            noise_level=0.5,
        )

        assert streamer.sample_rate == 0.1
        assert streamer.points_per_frame == 50
        assert streamer.noise_level == 0.5

    def test_generate_frame(self) -> None:
        streamer = DataStreamer(points_per_frame=50)

        frame = streamer.generate_frame()

        assert isinstance(frame, DataFrame)
        assert frame.timestamp == 0.0
        assert len(frame.x) == 50
        assert len(frame.y) == 50

    def test_generate_multiple_frames_advances_time(self) -> None:
        streamer = DataStreamer()

        frame1 = streamer.generate_frame()
        frame2 = streamer.generate_frame()
        frame3 = streamer.generate_frame()

        assert frame1.timestamp == 0.0
        assert frame2.timestamp == 0.1
        assert frame3.timestamp == 0.2

    def test_reset(self) -> None:
        streamer = DataStreamer()
        streamer.generate_frame()
        streamer.generate_frame()

        streamer.reset()

        assert streamer.time == 0.0
        frame = streamer.generate_frame()
        assert frame.timestamp == 0.0

    def test_data_is_sine_wave_with_noise(self) -> None:
        streamer = DataStreamer(noise_level=0.0, points_per_frame=100)

        frame = streamer.generate_frame()

        # Without noise, y should be exactly sin(x)
        expected_y = np.sin(frame.x)
        np.testing.assert_array_almost_equal(frame.y, expected_y)
