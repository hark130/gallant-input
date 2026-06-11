"""Defines the class for Binary Phase Shift Key (BPSK) MOdulation/DEModulation."""

# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import (convert_ascii_bin_bytes_to_bits, map_bits_to_symbols,
                                 stringify_ndarray, upsample)
from gallant_input.modem.calc import (compute_threshold, extract_bits_from_samples,
                                      extract_bits_from_single_cluster)
from gallant_input.modem.bpsk_config import BPSKConfig
from gallant_input.modem.constants import BPSK_MAP
from gallant_input.modem.modem import Modem
from gallant_input.modem.threshold_scheme import ThresholdScheme
from gallant_input.validation import validate_bool, validate_ndarray, validate_pos_int


class BPSK(Modem):
    """Modulate and demodulate BPSK digital signals."""

    # CORE METHODS

    def __init__(self, config: BPSKConfig):
        """Class ctor.

        Args:
            config: Necessary configuration settings.
        """
        self._bits_per_sym = 1  # Bits per symbol
        super().__init__(config=config)

    # ABSTRACT METHODS

    def modulate(self, bin_bytes: bytes, mapper: dict[int, complex] = BPSK_MAP) -> numpy.ndarray:
        """MOdulate binary data.

        Args:
            bin_bytes: A bytes object containing binary to modulate.
            mapper: [OPTIONAL] The bits --> symbol dictionary.

        Returns:
            The modulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value (e.g., "...and I thought I saw a 2" -Bender).
        """
        # LOCAL VARIABLES
        iq = None  # Complex samples modulated from bin_bytes

        # VALIDATION        
        self.parse()  # Validate and parse

        # MODULATE IT
        bits = convert_ascii_bin_bytes_to_bits(bin_bytes)
        symbols = map_bits_to_symbols(bits, bits_per_symbol=self._bits_per_sym, mapper=mapper)
        waveform = upsample(symbols, self._sps)
        iq = waveform.astype(numpy.complex64)

        # DONE
        return iq

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
        # LOCAL VARIABLES
        bits = None       # An array of bits extracted from samples
        bit_stream = b''  # The bits as a bin bytes object

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=False)

        # DEMODULATE IT

        # bit_stream = stringify_ndarray(bits)

        # DONE
        return bit_stream

    # PUBLIC METHODS

# I'm not (yet) comfortable moving this code up to Modem() because I suspect I'll have to
# special-case something in a future child class.
# pylint: disable = duplicate-code
    def parse(self) -> None:
        """Validate, parse and update attributes once.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
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
# pylint: enable = duplicate-code

    # PRIVATE METHODS

    def _parse(self) -> None:
        """Parse user input."""
        self._parse_abc()

    def _validate(self) -> None:
        """Validate attribute values."""
        self._validate_abc()
        validate_pos_int(self._bits_per_sym, 'internal attribute _bits_per_sym')
