"""Data streaming and generation."""

from dataclasses import dataclass, field

import numpy as np


@dataclass
class DataFrame:
    """A single frame of streaming data."""

    timestamp: float
    x: np.ndarray
    y: np.ndarray

    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "type": "data",
            "timestamp": self.timestamp,
            "shape": list(self.y.shape),
            "dtype": str(self.y.dtype),
            "x": self.x.tolist(),
            "y": self.y.tolist(),
        }


@dataclass
class DataStreamer:
    """Generates streaming data frames.

    In production, this would interface with actual sensors or data sources.
    """

    sample_rate: float = 0.05  # seconds between frames
    points_per_frame: int = 100
    noise_level: float = 0.1
    _t: float = field(default=0.0, init=False, repr=False)

    def generate_frame(self) -> DataFrame:
        """Generate a single data frame (sine wave with noise)."""
        x = np.linspace(self._t, self._t + 2 * np.pi, self.points_per_frame)
        y = np.sin(x) + self.noise_level * np.random.randn(self.points_per_frame)

        frame = DataFrame(timestamp=self._t, x=x, y=y)
        self._t += 0.1
        return frame

    def reset(self) -> None:
        """Reset the time counter."""
        self._t = 0.0

    @property
    def time(self) -> float:
        """Current timestamp."""
        return self._t
