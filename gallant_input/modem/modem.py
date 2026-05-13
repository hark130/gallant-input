"""Defines the abstract base class (ABC) for MOdulation/DEModulation."""


# Standard Imports
from abc import ABC, abstractmethod
# Third Party Imports
import numpy
# Local Imports
from gallant_input.modem.calc import calculate_sps
from gallant_input.validation import validate_bool, validate_pos_float_or_int


class Modem(ABC):
    """Abstract base class (ABC) for modulation and demodulation."""

    def __init__(self, sample_rate: float | int, symbol_rate: float | int, *args, **kwargs):
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
        super().__init__(*args, **kwargs)

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

    # PRIVATE METHODS

    def _parse_abc(self) -> None:
        """Parse user input defined in the ABC."""
        # PARSE IT
        self._sps = calculate_sps(self.sample_rate, self.symbol_rate)

    def _validate_abc(self) -> None:
        """Validate attribute values in the ABC."""
        validate_pos_float_or_int(self.sample_rate, 'sample_rate')
        validate_pos_float_or_int(self.symbol_rate, 'symbol_rate')
        validate_bool(self._parsed, 'internal attribute _parsed')
        # self._sps may not be valid yet so skip it
        # Not checking self._validated here so skip it
