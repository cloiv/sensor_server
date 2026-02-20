"""Numpy array processing utilities."""

import io

import numpy as np


def load_array_from_bytes(data: bytes) -> np.ndarray:
    """Load a numpy array from .npy file bytes.

    Args:
        data: Raw bytes from a .npy file

    Returns:
        The loaded numpy array

    Raises:
        ValueError: If the data is not a valid .npy file
    """
    buffer = io.BytesIO(data)
    try:
        return np.load(buffer, allow_pickle=False)
    except Exception as e:
        raise ValueError(f"Invalid numpy file: {e}") from e


def array_to_bytes(array: np.ndarray) -> bytes:
    """Convert a numpy array to .npy file bytes.

    Args:
        array: Numpy array to convert

    Returns:
        Raw bytes in .npy format
    """
    buffer = io.BytesIO()
    np.save(buffer, array)
    buffer.seek(0)
    return buffer.read()


def array_to_dict(array: np.ndarray) -> dict:
    """Convert a numpy array to a JSON-serializable dictionary.

    Args:
        array: Numpy array to convert

    Returns:
        Dictionary with shape, dtype, and data
    """
    return {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
        "data": array.tolist(),
    }


def array_metadata(array: np.ndarray) -> dict:
    """Get metadata for a numpy array.

    Args:
        array: Numpy array

    Returns:
        Dictionary with shape and dtype
    """
    return {
        "shape": list(array.shape),
        "dtype": str(array.dtype),
    }
