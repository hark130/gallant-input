"""Defines the MatchedFilter class."""

# Standard Imports
# Third Party Imports
from scipy.signal import lfilter
import numpy as np
# Local Imports


class MatchedFilter:
    """Maintain state while applying matched filter taps to signal chunks."""

    def __init__(self, taps: np.ndarray):
        """Class ctor."""
        self._taps = taps.astype(np.float32)
        # Initial conditions for the filter delays.
        self._state = np.zeros(len(taps) - 1, dtype=np.complex64)

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Apply the matched filter taps to a chunk of samples, maintaining filter delay values."""
        # Output of the digital filter, final filter delay values
        output, self._state = lfilter(self._taps, 1.0, chunk, zi=self._state)
        return output
