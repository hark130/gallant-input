"""Defines the class for Binary Frequency Shift Key (FSK) MOdulation/DEModulation."""

# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, stringify_ndarray
from gallant_input.modem.calc import reshape_to_symbols
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modem.modem import Modem
from gallant_input.modem.ook_config import OOKConfig
from gallant_input.validation import (validate_binary_bytes, validate_bool, validate_int_or_float,
                                      validate_ndarray, validate_phase, validate_type)


class FSK2(Modem):
    """Modulate and demodulate BFSK digital signals."""

    # CORE METHODS

    def __init__(self, config: FSK2Config):
        """Class ctor.

        Args:
            config: Necessary configuration settings.
        """
        self.freq0 = None         # The 'off' frequency baseband deviation.
        self.freq1 = None         # The 'on' frequency baseband deviation.
        self._phase = float(0.0)  # Phase state
        super().__init__(config=config)

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
        # LOCAL VARIABLES
        bits = None      # The binary bytes object converted at a numpy.ndarray
        freqs = None     # The bits array converted to on/off frequencies
        phase_inc = 0.0  # The amount to increase the phase by
        phi = None       # The new angle
        out = []         # Running list of samples
        iq = None        # Final array of modulated samples

        # VALIDATION
        self.parse()  # Validate and parse
        _validate_bin_bytes(bin_bytes=bin_bytes)

        # MODULATE IT
        bits = convert_ascii_bin_bytes_to_bits(bin_bytes)
        freqs = numpy.where(bits == 0, self.freq0, self.freq1)
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
        self.parse(demod=True)  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=True)

        # DEMODULATE IT
        dphi = numpy.angle(samples * numpy.conj(numpy.roll(samples, 1)))
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

    def parse(self, demod: bool = False) -> None:
        """Validate, parse and update attributes once.

        Args:
            demod: [OPTIONAL] Controls internal parsing/validation.  If True, the ctor config
                is parsed as a OOKConfig, instead of a FSK2Config, because demodulation doesn't
                require FSK2Config-specific values.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # VALIDATION
        validate_bool(self._parsed, 'internal attribute _parsed')
        validate_bool(demod, 'demod')
        self.validate(demod=demod)
        # PARSE IT
        if not self._parsed:
            self._parse()
            self._parsed = True

    def validate(self, demod: bool = False) -> None:
        """Validate attribute values once.

        Args:
            demod: [OPTIONAL] Controls internal parsing/validation.  If True, FSK2Config only
                validates the attributes necessary to demodulate a signal.

        Raises:
            TypeError: Bad data type.
            ValueError: Badd value.
        """
        # VALIDATION
        validate_bool(self._validated, 'internal attribute _validated')
        validate_bool(demod, 'demod')
        self._config.set_demod(demod=demod)
        if not self._validated:
            self._validate(demod=demod)
            self._validated = True

    # PRIVATE METHODS

    def _parse(self) -> None:
        """Parse user input."""
        self._parse_abc()
        self._parse_fsk2_config()  # Get the rest of the data from the child object

    def _parse_fsk2_config(self) -> None:
        """Gently extract config values into instance attributes."""
        if isinstance(self._config, FSK2Config):
            self.freq0 = self._config.freq0
            self.freq1 = self._config.freq1
            if self._config.phase is not None:
                self._update_phase(self._config.phase, pre_validate=True)  # Check it first

    def _update_phase(self, new_phase: float, pre_validate: bool = False) -> None:
        """Trim and update the phase attribute."""
        validate_bool(pre_validate, 'pre_validate')
        if pre_validate:
            validate_phase(new_phase, 'new_phase')
        self._phase = numpy.mod(new_phase, 2 * numpy.pi)

    def _validate(self, demod: bool) -> None:
        """Validate attribute values."""
        self._validate_abc()
        self._validate_fsk2_config(demod=demod)
        self._validate_phase()

    def _validate_fsk2_config(self, demod: bool) -> None:
        """Validate the FSK2Config object."""
        validate_bool(demod, 'demod')
        validate_type(self._config, 'config', FSK2Config)
        self._config.set_demod(demod=demod)
        self._config.validate_content()
        if demod is False:
            # Frequencies don't matter for demodualation
            _validate_frequencies(symbol_rate=self._config.symbol_rate,
                                  freq0=self._config.freq0, freq1=self._config.freq1)

    def _validate_phase(self) -> None:
        """Validate _phase attribute."""
        validate_phase(phase=self._phase, param_name='internal phase attribute')


def _validate_bin_bytes(bin_bytes: bytes) -> None:
    """Validate bin bytes, as non-empty, prior to conversion."""
    validate_binary_bytes(bin_bytes, 'bin_bytes', exact_len=None)
    if not bin_bytes:
        raise ValueError('The "bin_bytes" argument may not be empty')

def _validate_frequencies(symbol_rate: float | int,
                          freq0: float | int, freq1: float | int) -> None:
    """Validate the frequencies under their own strength and against each other."""
    min_dev = 0.5 * symbol_rate  # Minimum deviation between the two freqs
    validate_int_or_float(freq0, 'freq0')
    validate_int_or_float(freq1, 'freq1')
    freq_dev = abs(freq0 - freq1)
    if freq_dev < min_dev:
        raise ValueError(f'The deviation between "{freq0}" and "{freq1}" must be at '
                         f'*least* "{min_dev}"')
