"""Unit tests for core.storage module."""

import numpy as np
import pytest

from sensor_server.core.storage import ArrayStorage


class TestArrayStorage:
    """Tests for ArrayStorage class."""

    def test_empty_storage(self) -> None:
        storage = ArrayStorage()
        assert storage.count() == 0
        assert len(storage) == 0
        assert storage.list_all() == []

    def test_add_array(self) -> None:
        storage = ArrayStorage()
        arr = np.array([1, 2, 3])

        index = storage.add(arr)

        assert index == 0
        assert storage.count() == 1

    def test_add_multiple_arrays(self) -> None:
        storage = ArrayStorage()
        arr1 = np.array([1, 2, 3])
        arr2 = np.array([[1, 2], [3, 4]])

        idx1 = storage.add(arr1)
        idx2 = storage.add(arr2)

        assert idx1 == 0
        assert idx2 == 1
        assert storage.count() == 2

    def test_get_array(self) -> None:
        storage = ArrayStorage()
        arr = np.array([1.0, 2.0, 3.0])
        storage.add(arr)

        result = storage.get(0)

        assert result is not None
        np.testing.assert_array_equal(result, arr)

    def test_get_nonexistent_array(self) -> None:
        storage = ArrayStorage()

        assert storage.get(0) is None
        assert storage.get(-1) is None
        assert storage.get(100) is None

    def test_list_all(self) -> None:
        storage = ArrayStorage()
        storage.add(np.array([1, 2, 3], dtype=np.int32))
        storage.add(np.array([[1.0, 2.0]], dtype=np.float64))

        result = storage.list_all()

        assert len(result) == 2
        assert result[0] == {"index": 0, "shape": [3], "dtype": "int32"}
        assert result[1] == {"index": 1, "shape": [1, 2], "dtype": "float64"}

    def test_clear(self) -> None:
        storage = ArrayStorage()
        storage.add(np.array([1, 2, 3]))
        storage.add(np.array([4, 5, 6]))

        storage.clear()

        assert storage.count() == 0
        assert storage.get(0) is None

    def test_iteration(self) -> None:
        storage = ArrayStorage()
        arrays = [np.array([1]), np.array([2]), np.array([3])]
        for arr in arrays:
            storage.add(arr)

        result = list(storage)

        assert len(result) == 3
        for orig, stored in zip(arrays, result):
            np.testing.assert_array_equal(orig, stored)
