"""Defines the abstract base class (ABC) for MOdulation/DEModulation."""


# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, map_bits_to_symbols, upsample
from gallant_input.modem.constants import OOK_MAP
from gallant_input.modem.modem import Modem
from gallant_input.validation import validate_bool, validate_ndarray


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
        self.parse()  # Validate and parse
        bits = convert_ascii_bin_bytes_to_bits(bin_bytes)
        symbols = map_bits_to_symbols(bits, bits_per_symbol=1, mapper=OOK_MAP)
        waveform = upsample(symbols, self._sps)
        iq = waveform.astype(numpy.complex64)
        return iq

    def demodulate(self, samples: numpy.ndarray, threshold: float | None = None) -> bytes:
        """DEMoodulate binary data.

        Args:
            samples: Digital samples to demodulate.
            threshold: [OPTIONAL] Magnitude threshold used to decide between binary results.
                If None, automatically determine the threshold.

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        num_symbols = 0  # Number of complete symbols, valid or not, available in samples
        symbols = None   # ndarray of trimmed samples reshaped into symbols

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=False)

        # DEMODULATE IT
        # Trim it
        num_symbols = len(samples) // self._sps
        samples = samples[:num_symbols * self._sps]
        # Reshape it
        symbols = samples.reshape(-1, self._sps)



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
        self._parse_abc()

    def _validate(self) -> None:
        """Validate attribute values."""
        self._validate_abc()
