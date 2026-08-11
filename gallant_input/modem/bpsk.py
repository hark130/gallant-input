"""Defines the class for Binary Phase Shift Key (BPSK) MOdulation/DEModulation."""

# Standard Imports
# Third Party Imports
from sklearn.cluster import KMeans
import numpy
# Local Imports
from gallant_input.modem.calc import reshape_to_symbols
from gallant_input.codec import (convert_ascii_bin_bytes_to_bits, map_bits_to_symbols,
                                 stringify_ndarray, upsample)
from gallant_input.convolvemode import ConvolveMode
from gallant_input.filters import apply_fir, create_rect_fir, create_rrc_fir
from gallant_input.modem.bpsk_config import BPSKConfig
from gallant_input.modem.constants import BPSK_MAP
from gallant_input.modem.modem import Modem
from gallant_input.modem.matched_filter import MatchedFilter
from gallant_input.validation import (validate_bool, validate_mapper, validate_ndarray,
                                      validate_pos_int, validate_type)


class BPSK(Modem):
    """Modulate and demodulate BPSK digital signals."""

    # CORE METHODS

    def __init__(self, config: BPSKConfig):
        """Class ctor.

        Args:
            config: Necessary configuration settings.
        """
        super().__init__(config=config)
        self._bits_per_sym = 1         # Set bits per symbol
        self._carrier_recovery = None  # Optional carrier recovery object

    # ABSTRACT METHODS

    def modulate(self, bin_bytes: bytes, mapper: dict[int, complex] = None) -> numpy.ndarray:
        """MOdulate binary data.

        Args:
            bin_bytes: A bytes object containing binary to modulate.
            mapper: [OPTIONAL] The bits --> symbol dictionary.  If None, defaults to
                BPSK_MAP (see: gallant_input.modem.constants).

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

        # SETUP
        if mapper is None:
            mapper = BPSK_MAP

        # MODULATE IT
        bits = convert_ascii_bin_bytes_to_bits(bin_bytes)
        symbols = map_bits_to_symbols(bits, bits_per_symbol=self._bits_per_sym, mapper=mapper)
        waveform = upsample(symbols, self._sps)
        iq = waveform.astype(numpy.complex64)

        # DONE
        return iq

    def demodulate(self, samples: numpy.ndarray, filt: MatchedFilter = MatchedFilter.NONE,
                   mapper: dict[int, complex] | None = None) -> bytes:
        """DEMoodulate binary data.

        Args:
            samples: Digital samples to demodulate.
            filt: [OPTIONAL] The matched filter to apply.  MatchedFilter.RECT_FIR may be the
                optimal matched filter for a modulator that did not do any pulse shaping but
                the default is MatchedFilter.NONE (no matched filter applied).
            mapper: [OPTIONAL] The bits --> symbol dictionary.  If None, defaults to
                BPSK_MAP (see: gallant_input.modem.constants).

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        metric = None          # A continuous-valued symbol metric sampled at the input sample rate
        symbol_metrics = None  # One recovered symbol metric for each transmitted symbol
        bit_stream = b''       # The demodulated binary as a bytes object

        # SETUP
        if mapper is None:
            mapper = BPSK_MAP

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=False)
        validate_type(filt, 'filt', MatchedFilter)
        validate_mapper(mapper, 'mapper', self._bits_per_sym)

        # DEMODULATE IT
        # Step 1: Demodulate to metrics
        metric = self.demodulate_to_metric(samples=samples, filt=filt, mapper=mapper)
        # Step 2: Recover symbols
        symbol_metrics = self.recover_symbols(metric=metric)
        # Step 3: Decide symbols
        bit_stream = self.decide_symbols(symbol_metrics, mapper=mapper)

        # DONE
        return bit_stream

    # DEMODULATION STEPS
    # Step 1: Demodulate to metrics

    def demodulate_to_metric(self, samples: numpy.ndarray,
                             filt: MatchedFilter = MatchedFilter.NONE,
                             mapper: dict[int, complex] | None = None) -> numpy.ndarray:
        """DEModulate complex baseband samples to continuous-valued symbol metrics (Demod Step 1/3).

        Summary: Produces a continuous-valued representation in which the modulation's symbol
        information is explicit.

        This method performs the modulation-specific front-end of the demodulation process.
        The returned symbol metric retains the input sample rate and typically contains multiple
        samples per transmitted symbol.

        No symbol timing recovery or symbol decisions are performed by this method.
        The output is intended to be processed by a timing synchronization algorithm
        (e.g., synch.timing.recover_clock_mm(), self.recover_symbols()) before being converted
        into bits or symbols.

        Args:
            samples: Complex baseband IQ samples to demodulate.
            filt: [OPTIONAL] The matched filter to apply.  MatchedFilter.RECT_FIR may be the
                optimal matched filter for a modulator that did not do any pulse shaping but
                the default is MatchedFilter.NONE (no matched filter applied).
            mapper: [OPTIONAL] The bits --> symbol dictionary.  If None, defaults to
                BPSK_MAP (see: gallant_input.modem.constants).

        Returns:
            A continuous-valued symbol metric sampled at the input sample rate
            (e.g., one value per original sample).

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        corrected = None  # A carrier-recovered copy of samples (if an object was provided)
        filtered = None   # A match filtered applied to the samples (as specified)
        polar_diff = 0    # Difference between the mapper's complex values
        deriv_axis = 0    # Derived axis based on the mapper
        metric = None     # Continuous-valued symbol metric

        # SETUP
        if mapper is None:
            mapper = BPSK_MAP

        # INPUT VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=True)
        validate_type(filt, 'filt', MatchedFilter)
        validate_mapper(mapper, 'mapper', self._bits_per_sym)

        # DEMODULATE IT
        # Carrier recovery?
        if self._carrier_recovery is not None:
            corrected = self._carrier_recovery.process(samples)
        else:
            corrected = samples  # No recovery object
        # Receiver matched filter
        filtered = self._apply_matched_filter(samples=corrected, filt=filt)
        # Derive the decision axis from the mapper
        polar_diff = mapper[1] - mapper[0]
        deriv_axis = polar_diff / abs(polar_diff)
        # Continuous decision metric
        metric = (filtered * numpy.conj(deriv_axis)).real.astype(numpy.float32)

        # DONE
        return metric

    # Step 2: Recover symbols

    def recover_symbols(self, metric: numpy.ndarray) -> numpy.ndarray:
        """Recover one symbol metric for each transmitted symbol (Demod Step 2/3).

        Summary: Determines the optimal sampling instants and produces one value per
        transmitted symbol.

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
        self.parse()  # Validate and parse
        validate_ndarray(array=metric, array_name='metric', can_be_empty=False, num_dim=1,
                         must_be_complex=False)

        # RECOVER IT
        symbol_metrics = reshape_to_symbols(metric, self._sps).mean(axis=1)

        # DONE
        return symbol_metrics

    # Step 3: Decide symbols

    def decide_symbols(self, symbol_metrics: numpy.ndarray,
                       mapper: dict[int, complex] | None = None) -> bytes:
        """Convert recovered symbol metrics into digital symbol decisions (Demod Step 3/3).

        Summary: Map each recovered symbol value to the discrete symbol/bit representation.

        Maps each recovered symbol metric to its nearest valid symbol.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.
            mapper: [OPTIONAL] The bits --> symbol dictionary.  If None, defaults to
                BPSK_MAP (see: gallant_input.modem.constants).

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        threshold = 0.0  # The bit decision threshold
        polar_diff = 0   # Difference between the mapper's complex values
        deriv_axis = 0   # Derived axis based on the mapper
        bits = None      # The final array of 1s and 0s to convert to a bytes object
        bin_bytes = b''  # The final binary as a bytes object
        reshaped = None  # Reshaped symbol_metrics into a single column
        kmeans = None    # K-Means clustering object

        # SETUP
        if mapper is None:
            mapper = BPSK_MAP

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=symbol_metrics, array_name='symbol_metrics', can_be_empty=False,
                         num_dim=1, must_be_complex=False)
        validate_mapper(mapper, 'mapper', self._bits_per_sym)

        # DECIDE IT
        reshaped = symbol_metrics.reshape(-1, 1)  # Reshape symbol metrics into one multi-row column
        kmeans = KMeans(n_clusters=2)  # BFSK gets formed into two clusters
        kmeans.fit_predict(reshaped)  # Compute the cluster centers and predict indices
        centers = numpy.sort(kmeans.cluster_centers_.flatten())  # Collapse into a sorted 1-D array
        threshold = centers.mean()  # Average the center of the two clusters
        polar_diff = mapper[1] - mapper[0]
        deriv_axis = polar_diff / abs(polar_diff)
        point0 = (mapper[0] * numpy.conj(deriv_axis)).real
        point1 = (mapper[1] * numpy.conj(deriv_axis)).real
        bits = (symbol_metrics > threshold).astype(numpy.uint8) if point1 > point0 \
            else (symbol_metrics <= threshold).astype(numpy.uint8)
        bin_bytes = stringify_ndarray(bits)

        # DONE
        return bin_bytes

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
            ValueError: Bad value.
        """
        # VALIDATION
        validate_bool(self._validated, 'internal attribute _validated')
        if not self._validated:
            self._validate()
            self._validated = True
# pylint: enable = duplicate-code

    # PRIVATE METHODS

    def _apply_matched_filter(self, samples: numpy.ndarray, filt: MatchedFilter) -> numpy.ndarray:
        """Apply a matched filter to samples."""
        # LOCAL VARIABLES
        taps = None      # An array of matched filter taps
        filtered = None  # The samples array with a filter applied

        # APPLY IT
        match filt:
            case MatchedFilter.NONE:
                filtered = samples
            case MatchedFilter.RECT_FIR:
                taps = create_rect_fir(self._sps)
            case MatchedFilter.RRC:
                taps = create_rrc_fir(self._sps)
            # case MatchedFilter.RAIS_COS:
            # case MatchedFilter.GAUSS:
            case _:
                raise NotImplementedError(f'No support for "MatchedFilter.{filt.name}" yet')
        if taps is not None:
            filtered = apply_fir(samples=samples, coeffs=taps, mode=ConvolveMode.SAME)

        # DONE
        return filtered

    def _parse(self) -> None:
        """Parse user input."""
        self._parse_abc()
        self._parse_bpsk_config()  # Get the rest of the data from the child object

    def _parse_bpsk_config(self) -> None:
        """Gently extract config values into instance attributes."""
        validate_type(self._config, 'config', BPSKConfig)
        self._config.validate_content()
        self._carrier_recovery = self._config.carrier_recovery

    def _validate(self) -> None:
        """Validate attribute values."""
        self._validate_abc()
        validate_pos_int(self._bits_per_sym, 'internal attribute _bits_per_sym')
