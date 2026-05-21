"""Defines the class for Binary Frequency Shift Key (FSK) MOdulation/DEModulation."""

# Standard Imports
import math
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, stringify_ndarray
from gallant_input.modem.calc import reshape_to_symbols
from gallant_input.modem.modem import Modem
from gallant_input.validation import (validate_binary_bytes, validate_bool, validate_float,
                                      validate_int_or_float, validate_ndarray)


class FSK2(Modem):
    """Modulate and demodulate BFSK digital signals."""

    # CORE METHODS

    def __init__(self, *args, **kwargs):
        """Class ctor."""
        self._phase = float(0.0)  # Phase state
        super().__init__(*args, **kwargs)

    # ABSTRACT METHODS

    def modulate(self, bin_bytes: bytes, freq0: float | int, freq1: float | int,
                 phase: float | None = None) -> numpy.ndarray:
        """MOdulate binary data.

        Args:
            bin_bytes: A bytes object containing binary to modulate.
            freq0: The 'off' frequency baseband deviation.
            freq1: The 'on' frequency baseband deviation.
            phase: [OPTIONAL] Override the internal phase continuity.

        Returns:
            The modulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value (e.g., "...and I thought I saw a 2" -Bender).
        """
        # LOCAL VARIABLES
        bits = None      # The binary bytes object converted at a numpy.ndarray
        freqs = None     # The bits array converted to on/off frequencies
        phase_inc = 0.0  # The amount to increase the phase by
        phi = None       # The new angle
        out = []         # Running list of samples
        iq = None        # Final array of modulated samples

        # VALIDATION
        self.parse()  # Validate and parse
        self._validate_frequencies(freq0=freq0, freq1=freq1)
        _validate_bin_bytes(bin_bytes=bin_bytes)
        bits = convert_ascii_bin_bytes_to_bits(bin_bytes)
        if phase is not None:
            self._update_phase(phase, pre_validate=True)  # Check it prior to final update

        # MODULATE IT
        freqs = numpy.where(bits == 0, freq0, freq1)
        for freq in freqs:
            phase_inc = 2 * numpy.pi * freq / self.sample_rate
            phi = self._phase + phase_inc * numpy.arange(self._sps)
            out.append(numpy.exp(1j * phi))
            self._update_phase(phi[-1] + phase_inc)  # Maintain a continuous phase
        iq = numpy.concatenate(out).astype(numpy.complex64)

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
        bit_stream = b''  # The bits as a bin bytes object
        dphi = None       # The difference between angles
        symbols = None    # An ndarray of trimmed samples reshaped to samples per symbol
        bits = None       # An array of bits extracted from samples

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=True)

        # DEMODULATE IT
        # dphi = numpy.angle(samples[1:] * numpy.conj(samples[:-1]))  # ORIGINAL
        dphi = numpy.angle(samples * numpy.conj(numpy.roll(samples, 1)))  # FIX(?)
        dphi[0] = dphi[1]  # Padding the first sample
        symbols = reshape_to_symbols(dphi, self._sps).mean(axis=1)
        bits = (symbols > 0).astype(numpy.uint8)
        bit_stream = stringify_ndarray(bits)

        # DONE
        return bit_stream

    # PUBLIC METHODS

    def get_phase(self) -> float:
        """Fetch the current phase."""
        self.parse()  # Validate and parse
        self._validate_phase()  # Check it again just to be sure
        return self._phase

# I'm not (yet) comfortable moving this code up to Modem() because I suspect I'll have to
# special-case something in a future child class.
# pylint: disable = duplicate-code
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
# pylint: enable = duplicate-code

    # PRIVATE METHODS

    def _parse(self) -> None:
        """Parse user input."""
        self._parse_abc()

    def _update_phase(self, new_phase: float, pre_validate: bool = False) -> None:
        """Trim and update the phase attribute."""
        validate_bool(pre_validate, 'pre_validate')
        if pre_validate:
            _validate_phase(new_phase, 'new_phase')
        self._phase = numpy.mod(new_phase, 2 * numpy.pi)

    def _validate(self) -> None:
        """Validate attribute values."""
        self._validate_abc()
        self._validate_phase()

    def _validate_frequencies(self, freq0: float | int, freq1: float | int) -> None:
        """Validate the frequencies under their own strength and against each other."""
        min_dev = 0.5 * self.symbol_rate  # Minimum deviation between the two freqs
        validate_int_or_float(freq0, 'freq0')
        validate_int_or_float(freq1, 'freq1')
        freq_dev = abs(freq0 - freq1)
        if freq_dev < min_dev:
            raise ValueError(f'The deviation between "{freq0}" and "{freq1}" must be at '
                             f'*least* "{min_dev}"')

    def _validate_phase(self) -> None:
        """Validate _phase attribute."""
        _validate_phase(phase=self._phase, param_name='internal attribute _phase')


def _validate_bin_bytes(bin_bytes: bytes) -> None:
    """Validate bin bytes prior to conversion."""
    validate_binary_bytes(bin_bytes, 'bin_bytes', exact_len=None)
    if not bin_bytes:
        raise ValueError('The "bin_bytes" argument may not be empty')


def _validate_phase(phase: float, param_name: str) -> None:
    """Validate phase, as a SPOT, on behalf of this module."""
    upper_bound = 2 * math.pi  # Upper limit for self._phase
    validate_float(phase, param_name)
    if phase < 0:
        raise ValueError(f'The {param_name} value may not be negative: {phase}')
    if phase > upper_bound:
        raise ValueError(f'The {param_name} value may not be greater than {upper_bound}: '
                         f'{phase}')
