"""Defines the abstract base class (ABC) for MOdulation/DEModulation."""


# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import (convert_ascii_bin_bytes_to_bits, map_bits_to_symbols,
                                 stringify_ndarray, upsample)
from gallant_input.modem.calc import (compute_threshold, extract_bits_from_samples,
                                      extract_bits_from_single_cluster, trim_samples)
from gallant_input.modem.constants import OOK_MAP
from gallant_input.modem.modem import Modem
from gallant_input.modem.threshold_scheme import ThresholdScheme
from gallant_input.validation import validate_bool, validate_ndarray, validate_pos_float


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
        bits = None       # An array of bits extracted from samples
        bit_stream = b''  # The bits as a bin bytes object

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=False)
        if threshold is not None:
            validate_pos_float(threshold, 'threshold')
        else:
            # MIDRANGE is fine for OOK
            threshold = compute_threshold(samples, self._sps, scheme=ThresholdScheme.MIDRANGE)

        # DEMODULATE IT
        if threshold is not None:
            bits = extract_bits_from_samples(samples, self._sps, threshold)
        else:
            bits = extract_bits_from_single_cluster(samples, self._sps)
        bit_stream = stringify_ndarray(bits)

        # DONE
        return bit_stream


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
