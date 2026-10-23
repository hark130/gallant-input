"""Defines the MatchedFilter class."""

# Standard Imports
# Third Party Imports
from scipy.signal import lfilter
import numpy as np
# Local Imports
from protoroad.validation import validate_ndarray


# pylint: disable=too-few-public-methods
class MatchedFilter:
    """Maintain state while applying matched filter taps to signal chunks."""

    def __init__(self, taps: np.ndarray):
        """Class ctor."""
        self._taps = taps.astype(np.float32)
        # Initial conditions for the filter delays.
        self._state = np.zeros(len(taps) - 1, dtype=np.complex64)

    def process(self, chunk: np.ndarray) -> np.ndarray:
        """Apply the matched filter taps to a chunk of samples, maintaining filter delay values."""
        # LOCAL VARIABLES
        output = chunk

        # INPUT VALIDATION
        chunk = validate_ndarray(chunk, "chunk", dtype=np.complex64)

        # PROCESS IT
        if chunk.size > 0:
            # Output of the digital filter, final filter delay values
            output, self._state = lfilter(self._taps, 1.0, chunk, zi=self._state)

        # DONE
        return output
# pylint: enable=too-few-public-methods
