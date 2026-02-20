"""Array storage abstraction."""

from typing import Iterator

import numpy as np


class ArrayStorage:
    """In-memory storage for numpy arrays.

    In production, this could be backed by Redis, a database, or filesystem.
    """

    def __init__(self) -> None:
        self._arrays: list[np.ndarray] = []

    def add(self, array: np.ndarray) -> int:
        """Store an array and return its index."""
        self._arrays.append(array)
        return len(self._arrays) - 1

    def get(self, index: int) -> np.ndarray | None:
        """Get an array by index, or None if not found."""
        if 0 <= index < len(self._arrays):
            return self._arrays[index]
        return None

    def list_all(self) -> list[dict]:
        """List metadata for all stored arrays."""
        return [
            {"index": i, "shape": list(arr.shape), "dtype": str(arr.dtype)}
            for i, arr in enumerate(self._arrays)
        ]

    def count(self) -> int:
        """Return the number of stored arrays."""
        return len(self._arrays)

    def clear(self) -> None:
        """Remove all stored arrays."""
        self._arrays.clear()

    def __iter__(self) -> Iterator[np.ndarray]:
        return iter(self._arrays)

    def __len__(self) -> int:
        return len(self._arrays)
