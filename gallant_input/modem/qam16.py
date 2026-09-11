"""Defines the class for Quadrature Amplitude Modulation (QAM) MOdulation/DEModulation."""

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
from gallant_input.modem.decide_symbols import DecideSymbols
from gallant_input.modem.qam16_config import QAM16Config
from gallant_input.modem.modem import Modem
from gallant_input.modem.matched_filter import MatchedFilter
from gallant_input.validation import validate_bool, validate_ndarray, validate_type


class QAM16(Modem):
    """Modulate and demodulate 16-QAM digital signals."""

    # CORE METHODS

    def __init__(self, config: QAM16Config):
        """Class ctor.

        Args:
            config: Necessary configuration settings.
        """
        self._carrier_recovery = None  # Optional carrier recovery object
        self._mapper = None            # Bit map
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
        iq = None  # Complex samples modulated from bin_bytes

        # VALIDATION
        self.parse()  # Validate and parse

        # MODULATE IT
        bits = convert_ascii_bin_bytes_to_bits(bin_bytes)
        symbols = map_bits_to_symbols(bits, bits_per_symbol=self._bits_per_sym, mapper=self._mapper)
        waveform = upsample(symbols, self._sps)
        iq = waveform.astype(numpy.complex64)

        # DONE
        return iq

    def demodulate(self, samples: numpy.ndarray, filt: MatchedFilter = MatchedFilter.NONE,
                   symbol_strategy: DecideSymbols = DecideSymbols.NEAR) -> bytes:
        """DEMoodulate binary data.

        Args:
            samples: Digital samples to demodulate.
            filt: [OPTIONAL] The matched filter to apply.  MatchedFilter.RECT_FIR may be the
                optimal matched filter for a modulator that did not do any pulse shaping but
                the default is MatchedFilter.NONE (no matched filter applied).
            symbol_strategy: [OPTIONAL] The strategy to use to 'decide symbols'.  Default strategy
                is to find the nearest constellation point.

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        metric = None          # A complex-valued symbol metric sampled at the input sample rate
        symbol_metrics = None  # One recovered symbol metric for each transmitted symbol
        bit_stream = b''       # The demodulated binary as a bytes object

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=False)
        validate_type(filt, 'filt', MatchedFilter)
        validate_type(symbol_strategy, 'symbol_strategy', DecideSymbols)

        # DEMODULATE IT
        # Step 1: Demodulate to metrics
        metric = self.demodulate_to_metric(samples=samples, filt=filt)
        # Step 2: Recover symbols
        symbol_metrics = self.recover_symbols(metric=metric)
        # Step 3: Decide symbols
        bit_stream = self.decide_symbols(symbol_metrics, symbol_strategy=symbol_strategy)

        # DONE
        return bit_stream

    # DEMODULATION STEPS
    # Step 1: Demodulate to metrics

    def demodulate_to_metric(self, samples: numpy.ndarray,
                             filt: MatchedFilter = MatchedFilter.NONE) -> numpy.ndarray:
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
            filt: [OPTIONAL] The matched filter to apply.  MatchedFilter.RECT_FIR may be the
                optimal matched filter for a modulator that did not do any pulse shaping but
                the default is MatchedFilter.NONE (no matched filter applied).

        Returns:
            A Complex-valued symbol metric sampled at the input sample rate
            (e.g., one value per original sample).

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        corrected = None  # A carrier-recovered copy of samples (if an object was provided)
        filtered = None   # A matched filter applied to the samples (as specified)
        metric = None     # Complex-valued symbol metric

        # INPUT VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=True)
        validate_type(filt, 'filt', MatchedFilter)

        # DEMODULATE IT
        # Carrier recovery?
        if self._carrier_recovery is not None:
            corrected = self._carrier_recovery.process(samples)
        else:
            corrected = samples  # No recovery object
        # Receiver matched filter
        filtered = self._apply_matched_filter(samples=corrected, filt=filt)
        # Complex decision metric
        metric = filtered.astype(numpy.complex64)  # Maintain IQ info

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

        No symbol decisions are made by this method. The returned values remain complex-valued
        and are intended to be passed to self.decide_symbols().

        Args:
            metric: Complex-valued symbol metrics.

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
                         must_be_complex=True)

        # RECOVER IT
        symbol_metrics = reshape_to_symbols(metric, self._sps).mean(axis=1)

        # DONE
        return symbol_metrics

    # Step 3: Decide symbols

    def decide_symbols(self, symbol_metrics: numpy.ndarray,
                       symbol_strategy: DecideSymbols) -> bytes:
        """Convert recovered symbol metrics into digital symbol decisions (Demod Step 3/3).

        Summary: Map each recovered symbol value to the discrete symbol/bit representation.

        Maps each recovered symbol metric to its nearest valid symbol.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.
            symbol_strategy: The strategy to use to 'decide symbols'.

        Returns:
            The demodulated binary data.

        Raises:
            TypeError: Invalid data type.
            ValueError: Bad value (e.g., Not enough symbols in symbol_metrics).
        """
        # LOCAL VARIABLES
        n_symbols = 0         # 16 for 16-QAM
        symbol_values = None  # Decided mapper key per symbol
        bit_matrix = None     # Array of uint8 binary values
        bits = None           # The final array of 1s and 0s to convert to a bytes object
        bin_bytes = b''       # The final binary as a bytes object

        # VALIDATION
        self.parse()  # Validate and parse
        validate_ndarray(array=symbol_metrics, array_name='symbol_metrics', can_be_empty=False,
                         num_dim=1, must_be_complex=True)
        validate_type(symbol_strategy, 'symbol_strategy', DecideSymbols)
        n_symbols = 2 ** self._bits_per_sym  # 16 symbols for 16-QAM
        if len(symbol_metrics) < n_symbols:
            raise ValueError(f'Requires at least {n_symbols} symbols to cluster but received '
                             f'{len(symbol_metrics)}')

        # DECIDE IT
        match symbol_strategy:
            case DecideSymbols.AXIS:
                symbol_values = self._decide_symbols_axis(symbol_metrics=symbol_metrics)
            case DecideSymbols.KMEANS | DecideSymbols.KMEANS_GAIN:
                symbol_values = self._decide_symbols_kmeans(
                    symbol_metrics=symbol_metrics,
                    correct_gain=symbol_strategy is DecideSymbols.KMEANS_GAIN)
            case DecideSymbols.NEAR:
                symbol_values = self._decide_symbols_nearest(symbol_metrics=symbol_metrics)
            case _:
                raise NotImplementedError('No support for "DecideSymbols.'
                                          f'{symbol_strategy.name}" yet')
        if symbol_values is None or len(symbol_values) <= 0:
            raise RuntimeError(f'The DecideSymbols.{symbol_strategy.name} stragey failed')

        # 4. Unpack the symbol values into binary
        bit_matrix = ((symbol_values[:, None] >>
                       numpy.arange(self._bits_per_sym - 1, -1, -1)) & 1).astype(numpy.uint8)
        bits = bit_matrix.flatten()
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

    def _decide_symbols_axis(self, symbol_metrics: numpy.ndarray) -> numpy.ndarray:
        """Decide symbol values using the axis strategy.

        Quantize values to the nearest 16-QAM axis level.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.

        Returns:
            Symbol values to be unpacked into binary.
        """
        # LOCAL VARIABLES
        real_values = symbol_metrics.real               # Array of real values
        imag_values = symbol_metrics.imag               # Array of imaginary values
        real_metrics = _decide_axis(real_values)        # Real value symbol metrics
        imag_metrics = _decide_axis(imag_values)        # Imaginary value symbol metrics
        axis_points = real_metrics + 1j * imag_metrics  # Metrics glued back together
        reverse_mapper = {}                             # Reversed constellation diagram
        symbol_values = None                            # Array of symbol values to be unpacked

        # DECIDE IT
        reverse_mapper = {point: symbol for symbol, point in self._mapper.items()}
        symbol_values = numpy.asarray([reverse_mapper[point] for point in axis_points],
                                      dtype=numpy.uint8)

        # DONE
        return symbol_values

# pylint: disable=too-many-locals
    def _decide_symbols_kmeans(self, symbol_metrics: numpy.ndarray,
                               correct_gain: bool) -> numpy.ndarray:
        """Decide symbol values using the k-means strategy.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.
            correct_gain: Estimate and correct unknown channel gain if True.

        Returns:
            Symbol values to be unpacked into binary.
        """
        # LOCAL VARIABLES
        n_symbols = 2 ** self._bits_per_sym  # 16 for 16-QAM
        features = None                      # Stacked columns of real and imaginary symbol metrics
        kmeans = None                        # The KMeans() object
        labels = None                        # Array of cluster labels (not symbols)
        centers = None                       # Centroids
        label_to_key = {}                    # Cluster label -> mapper key
        symbol_values = None                 # Numpy array of symbol values ready to be unpacked

        # DECIDE IT
        # 1. Cluster in the complex plane
        features = numpy.column_stack([symbol_metrics.real, symbol_metrics.imag])
        kmeans = KMeans(n_clusters=n_symbols, n_init='auto')
        labels = kmeans.fit_predict(features)
        centers = kmeans.cluster_centers_[:, 0] + 1j * kmeans.cluster_centers_[:, 1]

        # 2. Estimate and correct unknown channel gain?
        if correct_gain is True:
            mapper_values = numpy.array(list(self._mapper.values()))
            observed_rms = numpy.sqrt(numpy.mean(numpy.abs(centers) ** 2))  # Actual RMS
            ideal_rms = numpy.sqrt(numpy.mean(numpy.abs(mapper_values) ** 2))  # Mapper's RMS
            if observed_rms == 0:
                raise ValueError('Observed constellation collapsed to the origin (zero RMS).  '
                                 'Cannot estimate channel gain')
            scale = ideal_rms / observed_rms
            centers_normalized = centers * scale  # Scale observed centers to mapper's fixed radii
        else:
            centers_normalized = centers  # Don't scale it

        # 3. Match each (normalized?) centroid to its nearest mapper entry
        for label, center in enumerate(centers_normalized):
            distances = {key: abs(center - value) for key, value in self._mapper.items()}
            label_to_key[label] = min(distances, key=distances.get)

        # 4. Resolve each sample's cluster label to its mapper key (0-15)
        symbol_values = numpy.array([label_to_key[label] for label in labels], dtype=numpy.uint8)

        # DONE
        return symbol_values
# pylint: enable=too-many-locals

    def _decide_symbols_nearest(self, symbol_metrics: numpy.ndarray) -> numpy.ndarray:
        """Decide symbol values using the which-constellation-point-is-nearest strategy.

        Quantize values to the nearest 16-QAM axis level.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.

        Returns:
            Symbol values to be unpacked into binary.
        """
        # LOCAL VARIABLES
        symbol_values = None  # Array of symbol values to be unpacked
        distances = None      # The distance from every received symbol to every constellation point
        nearest = None        # The shortest distance to a constellation point for each symbol
        # Array of symbol keys
        map_symbols = numpy.asarray(list(self._mapper.keys()), dtype=numpy.uint8)
        # Array containing the corresponding constellation points
        const_points = numpy.asarray(list(self._mapper.values()), dtype=numpy.complex64)

        # DECIDE IT
        distances = numpy.abs(symbol_metrics[:, None] - const_points[None, :])  # Calc distance
        nearest = numpy.argmin(distances, axis=1)  # Get the nearest values
        symbol_values = map_symbols[nearest]  # Convert the const. array indices back to symbol keys

        # DONE
        return symbol_values

    def _parse(self) -> None:
        """Parse user input."""
        self._parse_abc()
        self._parse_qam16_config()  # Get the rest of the data from the child object

    def _parse_qam16_config(self) -> None:
        """Gently extract config values into instance attributes."""
        validate_type(self._config, 'config', QAM16Config)
        self._config.validate_content()
        self._bits_per_sym = self._config.bits_per_sym
        self._carrier_recovery = self._config.carrier_recovery
        self._mapper = self._config.mapper

    def _validate(self) -> None:
        """Validate attribute values."""
        self._validate_abc()


def _decide_axis(metric_axis: numpy.ndarray) -> numpy.ndarray:
    """Decide symbol values using the axis strategy.

    Quantize values to the nearest 16-QAM axis level.

    Args:
        metric_axis: One recovered symbol metric for each transmitted symbol.

    Returns:
        Symbol values to be unpacked into binary.
    """
    # LOCAL VARIABLES
    symbol_values = None  # Numpy array of symbol values ready to be unpacked

    # DECIDE IT
    symbol_values = numpy.where(metric_axis < -2, -3,
                                numpy.where(metric_axis < 0, -1,
                                            numpy.where(metric_axis < 2, 1, 3,),),)

    # DONE
    return symbol_values
