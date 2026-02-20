"""Unit tests for core.processing module."""

import io

import numpy as np
import pytest

from sensor_server.core.processing import (
    load_array_from_bytes,
    array_to_bytes,
    array_to_dict,
    array_metadata,
)


class TestLoadArrayFromBytes:
    """Tests for load_array_from_bytes function."""

    def test_load_valid_array(self) -> None:
        original = np.array([1.0, 2.0, 3.0])
        buffer = io.BytesIO()
        np.save(buffer, original)
        data = buffer.getvalue()

        result = load_array_from_bytes(data)

        np.testing.assert_array_equal(result, original)

    def test_load_2d_array(self) -> None:
        original = np.array([[1, 2], [3, 4]], dtype=np.int32)
        buffer = io.BytesIO()
        np.save(buffer, original)
        data = buffer.getvalue()

        result = load_array_from_bytes(data)

        np.testing.assert_array_equal(result, original)
        assert result.dtype == np.int32

    def test_load_invalid_data_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid numpy file"):
            load_array_from_bytes(b"not a valid npy file")

    def test_load_empty_data_raises(self) -> None:
        with pytest.raises(ValueError):
            load_array_from_bytes(b"")


class TestArrayToBytes:
    """Tests for array_to_bytes function."""

    def test_roundtrip(self) -> None:
        original = np.array([1.0, 2.0, 3.0, 4.0, 5.0])

        data = array_to_bytes(original)
        result = load_array_from_bytes(data)

        np.testing.assert_array_equal(result, original)

    def test_preserves_dtype(self) -> None:
        original = np.array([1, 2, 3], dtype=np.float32)

        data = array_to_bytes(original)
        result = load_array_from_bytes(data)

        assert result.dtype == np.float32


class TestArrayToDict:
    """Tests for array_to_dict function."""

    def test_1d_array(self) -> None:
        arr = np.array([1, 2, 3], dtype=np.int64)

        result = array_to_dict(arr)

        assert result["shape"] == [3]
        assert result["dtype"] == "int64"
        assert result["data"] == [1, 2, 3]

    def test_2d_array(self) -> None:
        arr = np.array([[1.0, 2.0], [3.0, 4.0]])

        result = array_to_dict(arr)

        assert result["shape"] == [2, 2]
        assert result["dtype"] == "float64"
        assert result["data"] == [[1.0, 2.0], [3.0, 4.0]]


class TestArrayMetadata:
    """Tests for array_metadata function."""

    def test_metadata(self) -> None:
        arr = np.zeros((10, 20, 30), dtype=np.float32)

        result = array_metadata(arr)

        assert result == {"shape": [10, 20, 30], "dtype": "float32"}
