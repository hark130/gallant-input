"""Defines the abstract base class (ABC) for MOdulation/DEModulation."""


# Standard Imports
from abc import ABC, abstractmethod
# Third Party Imports
import numpy
# Local Imports
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.validation import validate_bool, validate_pos_float_or_int, validate_pos_int


class Modem(ABC):
    """Abstract base class (ABC) for modulation and demodulation."""

    def __init__(self, config: ModemConfig):
        """Class ctor.

        Args:
            sample_rate: The sample rate of the capture in Hz.
            symbol_rate: The number of symbols-per-second (1 / symbol time).
        """
        self.sample_rate = None  # Sample rate
        self.symbol_rate = None  # Symbol rate
        self._parsed = False     # Input parsed
        self._sps = 0            # Samples per symbol
        self._validated = False  # Validation status of attributes
        self._parse_abc_config(config=config)  # Gently update instance attributes from config

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
        # Immediately validate it
        validate_pos_int(self._sps, 'internally calculated samples per symbol')

    def _parse_abc_config(self, config: ModemConfig) -> None:
        """Gently extract config values into instance attributes."""
        try:
            if isinstance(config, ModemConfig):
                config.validate_content()
                self.sample_rate = config.sample_rate
                self.symbol_rate = config.symbol_rate
        except (TypeError, ValueError):
            pass  # Don't update or raise anything.  Subsequent method calls will catch it.

    def _validate_abc(self) -> None:
        """Validate attribute values in the ABC."""
        validate_pos_float_or_int(self.sample_rate, 'sample_rate')
        validate_pos_float_or_int(self.symbol_rate, 'symbol_rate')
        validate_bool(self._parsed, 'internal attribute _parsed')
        # self._sps may not be valid yet so skip it
        # Not checking self._validated here so skip it
