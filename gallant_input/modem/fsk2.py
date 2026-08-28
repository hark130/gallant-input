"""Defines the class for Binary Frequency Shift Key (FSK) MOdulation/DEModulation."""

# Standard Imports
# Third Party Imports
from sklearn.cluster import KMeans
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, stringify_ndarray
from gallant_input.filters import create_gaussian_pulse
from gallant_input.modem.calc import reshape_to_symbols
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modem.modem import Modem
from gallant_input.validation import (validate_binary_bytes, validate_bool, validate_int_or_float,
                                      validate_ndarray, validate_phase, validate_pos_float,
                                      validate_type)


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
        self._est_sps = float(0.0)  # Estimated samples per symbol
        super().__init__(config=config)

    # ABSTRACT METHODS

    def modulate(self, bin_bytes: bytes, gauss_bt: float | None = None) -> numpy.ndarray:
        """MOdulate binary data.

        Args:
            bin_bytes: A bytes object containing binary to modulate.
            gauss_bt: [OPTIONAL] Gaussian pulse shaping bandwidth-time product (0.3-0.5 typical).
                If None, modulates with rectangular NRZ symbols (original behavior).

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
        # for freq in freqs:
        #     phase_inc = 2 * numpy.pi * freq / self.sample_rate
        #     phi = self._phase + phase_inc * numpy.arange(self._sps)
        #     out.append(numpy.exp(1j * phi))
        #     self._update_phase(phi[-1] + phase_inc)  # Maintain a continuous phase
        # iq = numpy.concatenate(out).astype(numpy.complex64)
        if gauss_bt is None:
            for freq in freqs:
                phase_inc = 2 * numpy.pi * freq / self.sample_rate
                phi = self._phase + phase_inc * numpy.arange(self._sps)
                out.append(numpy.exp(1j * phi))
                self._update_phase(phi[-1] + phase_inc)  # Maintain a continuous phase
            iq = numpy.concatenate(out).astype(numpy.complex64)
        else:
            # Gaussian-smoothed frequency sequence
            iq = self._modulate_shaped(freqs=freqs, gauss_bt=gauss_bt)

        # DONE
        return iq

    def demodulate(self, samples: numpy.ndarray) -> bytes:
        """DEModulate complex baseband samples into binary data (Demod Steps 1-3).

        Demodulation process:
            Step 1: self.demodulate_to_metric()
            Step 2: self.recover_symbols()
            Step 3: self.decide_symbols()

        Step 2 assumes ideal symbol timing by sampling at the configured samples-per-symbol.
        If not, consider replacing this step with an external timing synchronization algorithm
        (e.g., synch.timing.recover_clock_mm()).

        Args:
            samples: Digital samples to demodulate.

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        metric = None          # Continuous-valued symbol metric sampled at the input sample rate
        symbol_metrics = None  # One recovered symbol metric for each transmitted symbol
        bit_stream = b''       # The bits as a bin bytes object

        # VALIDATION
        self.parse(demod=True)  # Validate and parse

        # DEMODULATE IT
        # Step 1: Demodulate to metrics (instantaneous frequency via differential phase)
        metric = self.demodulate_to_metric(samples=samples)
        # Step 2: Recover symbols
        symbol_metrics = self.recover_symbols(metric=metric)
        # Step 3: Decide symbols (make binary decisions from the soft bits)
        bit_stream = self.decide_symbols(symbol_metrics)

        # DONE
        return bit_stream

    # PUBLIC METHODS

    def decide_symbols(self, symbol_metrics: numpy.ndarray) -> bytes:
        """Convert recovered symbol metrics into digital symbol decisions (Demod Step 3/3).

        Maps each recovered symbol metric to its nearest valid symbol.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        threshold = 0.0  # The bit decision threshold
        bits = None      # The final array of 1s and 0s to convert to a bytes object
        bin_bytes = b''  # The final binary as a bytes object
        reshaped = None  # Reshaped symbol_metrics into a single column
        kmeans = None    # K-Means clustering object

        # VALIDATION
        self.parse(demod=True)  # Validate and parse
        validate_ndarray(array=symbol_metrics, array_name='symbol_metrics', can_be_empty=False,
                         num_dim=1, must_be_complex=False)

        # DECIDE IT
        # NOTE: Using the "mean()" of the symbol metrics wasn't sufficient to find the
        # best decision boundary between the two populations of symbol metrics for some
        # live captures.  Why?  The median shifts towards a dominant cluster if the bit counts
        # aren't equally distributed.
        reshaped = symbol_metrics.reshape(-1, 1)  # Reshape symbol metrics into one multi-row column
        kmeans = KMeans(n_clusters=2)  # BFSK gets formed into two clusters
        kmeans.fit_predict(reshaped)  # Compute the cluster centers and predict indices
        centers = numpy.sort(kmeans.cluster_centers_.flatten())  # Collapse into a sorted 1-D array
        threshold = centers.mean()  # Average the center of the two clusters
        bits = (symbol_metrics > threshold).astype(numpy.uint8)  # Make bit decisions
        bin_bytes = stringify_ndarray(bits)

        # DONE
        return bin_bytes

    def demodulate_to_metric(self, samples: numpy.ndarray) -> numpy.ndarray:
        """DEModulate complex baseband samples to continuous-valued symbol metrics (Demod Step 1/3).

        This method performs the modulation-specific front-end of the demodulation process.
        The returned symbol metric retains the input sample rate and typically contains multiple
        samples per transmitted symbol.

        No symbol timing recovery or symbol decisions are performed by this method.
        The output is intended to be processed by a timing synchronization algorithm
        (e.g., synch.timing.recover_clock_mm(), self.recover_symbols()) before being converted
        into bits or symbols.

        Args:
            samples: Complex baseband IQ samples to demodulate.

        Returns:
            A continuous-valued symbol metric sampled at the input sample rate.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        dphi = None  # The difference between angles (instantaneous frequency)

        # VALIDATION
        self.parse(demod=True)  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=True)

        # DEMODULATE IT
        # Instantaneous frequency via differential phase
        dphi = numpy.angle(samples * numpy.conj(numpy.roll(samples, 1)))
        dphi[:int(self._sps)] = dphi[int(self._sps)]  # Pad entire first symbol
        dphi = numpy.append(dphi, dphi[-1])  # Extend the tail to avoid dropping the last symbol

        # DONE
        return dphi

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

    def recover_symbols(self, metric: numpy.ndarray) -> numpy.ndarray:
        """Recover one symbol metric for each transmitted symbol (Demod Step 2/3).

        This method performs symbol timing recovery by selecting a single, representative metric
        value for each transmitted symbol.  The returned array is reduced from the input sample
        rate to the symbol rate.

        The default implementation assumes ideal symbol timing by sampling at the configured
        samples-per-symbol.  If not, consider using an external timing synchronization algorithm
        (e.g., synch.timing.recover_clock_mm()) in lieu of this step.

        No symbol decisions are made by this method. The returned values remain continuous-valued
        and are intended to be passed to self.decide_symbols().

        Args:
            metric: Continuous-valued symbol metrics.

        Returns:
            One recovered symbol metric for each transmitted symbol.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        symbol_metrics = None  # The recovered symbol metrics

        # VALIDATION
        self.parse(demod=True)  # Validate and parse
        validate_ndarray(array=metric, array_name='metric', can_be_empty=False, num_dim=1,
                         must_be_complex=False)

        # RECOVER IT
        symbol_metrics = reshape_to_symbols(metric, self._sps).mean(axis=1)

        # DONE
        return symbol_metrics

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

    def _modulate_shaped(self, freqs: numpy.ndarray, gauss_bt: float) -> numpy.ndarray:
        """Modulate a per-symbol frequency sequence with Gaussian pulse shaping.

        Args:
            freqs: One frequency value (freq0 or freq1) per symbol.
            gauss_bt: Gaussian pulse shaping bandwidth-time product (which must be positive).

        Returns:
            The modulated, pulse-shaped IQ samples.
        """
        # LOCAL VARIABLES
        rect_freqs = None             # Freqs held at the sample rate (rectangular NRZ)
        gaussian_taps = None          # The Gaussian pulse-shaping filter
        shaped_freqs = None           # rect_freqs after Gaussian pulse shaping
        phase_inc_per_sample = None   # Per-sample phase increment
        phi = None                    # The cumulative phase array
        iq = None                     # Final array of modulated samples

        # INPUT VALIDATION
        validate_pos_float(gauss_bt, 'gauss_bt')

        # SHAPE IT
        rect_freqs = numpy.repeat(freqs, int(self._sps))  # Rectangular hold, per-sample
        gaussian_taps = create_gaussian_pulse(gauss_bt=gauss_bt, sps=int(self._sps))
        shaped_freqs = numpy.convolve(rect_freqs, gaussian_taps, mode='same')

        # INTEGRATE THE SHAPED FREQUENCY SEQUENCE INTO A CONTINUOUS PHASE
        phase_inc_per_sample = 2 * numpy.pi * shaped_freqs / self.sample_rate
        phi = self._phase + numpy.cumsum(phase_inc_per_sample)
        iq = numpy.exp(1j * phi).astype(numpy.complex64)
        self._update_phase(phi[-1] + phase_inc_per_sample[-1])  # Maintain a continuous phase

        # DONE
        return iq

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
