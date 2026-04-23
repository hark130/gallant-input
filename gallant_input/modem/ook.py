"""Defines the abstract base class (ABC) for MOdulation/DEModulation."""


# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import convert_bytes_to_bits, map_bits_to_symbols
from gallant_input.modem.constants import OOK_MAP
from gallant_input.modem.modem import Modem
from gallant_input.validation import validate_bool, validate_pos_float


class OOK(Modem):
    """Modulate and demodulate OOK digital signals."""

    # ABSTRACT METHODS

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
        bits = convert_bytes_to_bits(bin_bytes)
        symbols = map_bits_to_symbols(bits, bits_per_symbol=1, mapper=OOK_MAP)

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

    # PUBLIC METHODS

    def parse(self) -> None:
        """Validate, parse and update attributes once.

        Raises:
            TypeError: Bad data type.
            ValueError: Badd value.
        """
        # VALIDATION
        validate_bool(self._parsed, 'internal attribute _parsed')
        self.validate()
        # PARSE IT
        if not self._parsed:
            self._parse()
            self._parsed = True

    def validate(self) -> None:
        """Validate attribute values once.

        Raises:
            TypeError: Bad data type.
            ValueError: Badd value.
        """
        # VALIDATION
        validate_bool(self._validated, 'internal attribute _validated')
        if not self._validated:
            self._validate()
            self._validated = True

    # PRIVATE METHODS

    def _parse(self) -> None:
        """Parse user input."""
        # PARSE IT
        self._sps = int(self.sample_rate * self.symbol_rate)

    def _validate(self) -> None:
        """Validate attribute values."""
        validate_pos_float(self.sample_rate, 'sample_rate')
        validate_pos_float(self.symbol_rate, 'symbol_rate')
        validate_bool(self._parsed, 'internal attribute _parsed')
        # self._sps may not be valid yet so skip it
        # Not checking self._validated here so skip it
