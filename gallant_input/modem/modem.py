"""Defines the abstract base class (ABC) for MOdulation/DEModulation."""


# Standard Imports
from abc import ABC, abstractmethod
# Third Party Imports
import numpy
# Local Imports


class Modem(ABC):
    """Abstract base class (ABC) for modulation and demodulation."""

    def __init__(self, sample_rate: float, symbol_rate: float):
        """Class ctor.

        Args:
            sample_rate: The sample rate of the capture in Hz.
            symbol_rate: The number of symbols-per-second (1 / symbol time).
        """
        self.sample_rate = sample_rate
        self.symbol_rate = symbol_rate
        self._parsed = False            # Input parsed
        self._sps = 0                   # Samples per symbol
        self._validated = False         # Validation status of attributes

    @abstractmethod
    def modulate(self, bin_bytes: bytes) -> numpy.ndarray:
        """MOdulate binary data.

        Args:
            bin_bytes: A bytes object containing binary to modulate.

        Returns:
            The modulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value (e.g., "...and I thought I saw a 2" -Bender).
        """

    @abstractmethod
    def demodulate(self, samples: numpy.ndarray) -> bytes:
        """DEMoodulate binary data.

        Args:
            samples: Digital samples to demodulate.

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
