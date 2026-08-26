"""Defines a stateful Coarse Frequency Correction (CFO) class: FrequencyCorrector."""

# Standard Imports
# Third Party Imports
import numpy
import scipy.signal
# Local Imports


class FrequencyCorrector:
    """Stateful CFO downconverter."""

    def __init__(self, sample_rate: float, freq_sep: float,
                 tolerance_hz: float = 2000.0, snr_threshold_db: float = 10.0,
                 lock_count: int = 5, lock_std_hz: float = 15.0, buffer_size: int = 30,
                 nperseg: int = 4096, sep_tolerance_hz: float = 100.0):
        """Initialize a stateful CFO detector/corrector.

        Args:
            sample_rate: The sample rate of the incoming samples, in Hz.
            freq_sep: The expected separation between the two FSK tones, in Hz.
            tolerance_hz: [OPTIONAL] How far from each tone's expected position to search for its
                peak, in Hz.
            snr_threshold_db: [OPTIONAL] Minimum peak-to-noise-floor ratio, in dB, for a candidate
                to qualify.
            lock_count: [OPTIONAL] Number of consistent, SNR-qualified candidates required to lock.
            lock_std_hz: [OPTIONAL] Maximum spread, in Hz, allowed within a candidate cluster
                to lock.
            buffer_size: [OPTIONAL] Maximum number of recent candidates retained while searching
                for a cluster.
            nperseg: [OPTIONAL] Welch PSD segment length, in samples. Larger values improve
                frequency resolution at the cost of time resolution.
            sep_tolerance_hz: [OPTIONAL] Maximum allowed deviation between the measured and
                expected tone separation before a candidate is rejected as a false pair.
        """
        self._sample_rate = sample_rate
        self._freq_sep = freq_sep
        self._tolerance_hz = tolerance_hz
        self._snr_threshold_db = snr_threshold_db
        self._lock_count = lock_count
        self._lock_std_hz = lock_std_hz
        self._buffer_size = buffer_size
        self._nperseg = nperseg
        self._sep_tolerance_hz = sep_tolerance_hz  # How close (peak1-peak0) must be to freq_sep

        self._cfo_hz = 0.0
        self._locked = False
        self._candidates = []
        self._phase = 0.0

    def debug_state(self) -> str:
        return (f'[CFO] locked={self._locked} cfo_hz={self._cfo_hz:.1f} '
                f'buffer_size={len(self._candidates)}')

    def process(self, samples: numpy.ndarray, noise_floor_db: float | None = None,
                debug: bool = False) -> numpy.ndarray:
        """Apply the current CFO correction to a chunk, updating lock state while unlocked.

        Before locking, attempts a measurement each call and checks the growing candidate
        buffer for a qualifying cluster. Once locked, the CFO estimate is held fixed and no
        further measurement is attempted. The correction itself uses a persistent phase
        accumulator so the mixing LO stays phase-continuous across chunk boundaries.

        Args:
            samples: The chunk of complex baseband samples to correct.
            noise_floor_db: [OPTIONAL] The known noise floor, in dB, passed through to the internal
                measurement step while still searching for a lock. Ignored once locked.
            debug: [OPTIONAL] If True, prints debug statements about CFO locks.

        Returns:
            The frequency-corrected samples, same dtype and length as the input.
        """
        if not self._locked:
            measured = self._measure(samples, noise_floor_db)
            if measured is not None:
                self._candidates.append(measured)
                if len(self._candidates) > self._buffer_size:
                    self._candidates.pop(0)

                cluster = self._find_cluster(self._candidates, self._lock_count, self._lock_std_hz)
                if cluster is not None:
                    self._cfo_hz = cluster
                    self._locked = True
                    if debug:
                        print(f'[CFO] Locked at {self._cfo_hz:.1f} Hz')
                else:
                    if debug:
                        print('[CFO] No cluster yet, '
                              f'buffer={[round(c, 1) for c in self._candidates]}')

        phase_inc = -2 * numpy.pi * self._cfo_hz / self._sample_rate
        phi = self._phase + phase_inc * numpy.arange(len(samples))
        corrected = samples * numpy.exp(1j * phi)
        self._phase = (phi[-1] + phase_inc) % (2 * numpy.pi)
        return corrected.astype(samples.dtype)

    @staticmethod
    def _find_cluster(candidates: list, lock_count: int, lock_std_hz: float) -> float | None:
        """Find the smallest contiguous run of lock_count sorted candidates within lock_std_hz.

        Sorts the buffer and slides a window of size lock_count across it, so a tight
        sub-cluster of consistent readings can be found even when scattered outliers are
        interleaved elsewhere in the buffer.

        Args:
            candidates: The buffer of recent SNR-qualified CFO candidates, in Hz.
            lock_count: The number of candidates required to form a qualifying cluster.
            lock_std_hz: The maximum spread, in Hz, allowed within a cluster.

        Returns:
            The median of the first qualifying cluster found, or None if no such cluster
            exists yet in the current buffer.
        """
        # LOCAL VARIABLES
        cluster_median = None  # Cluster median


        if len(candidates) >= lock_count:
            sorted_vals = sorted(candidates)
            for i in range(len(sorted_vals) - lock_count + 1):
                window = sorted_vals[i:i + lock_count]
                if window[-1] - window[0] <= lock_std_hz:
                    cluster_median = float(numpy.median(window))  # Found one...
                    break  # ...so stop looking

        # DONE
        return cluster_median

    def _measure(self, samples: numpy.ndarray, noise_floor_db: float | None) -> float | None:
        """Measure a candidate CFO from one chunk of samples, if a confident detection exists.

        Locates the two expected FSK tones via a Welch-averaged PSD, requires each to
        individually clear the SNR threshold, and confirms the two peaks are separated by
        close to freq_sep (CFO-invariant, since CFO shifts both tones equally) before
        accepting the measurement -- rejecting single-source artifacts that spill into both
        search windows and would otherwise look like a confident two-tone detection.

        Args:
            samples: The chunk of complex baseband samples to search for tones in.
            noise_floor_db: The known noise floor, in dB, on the same scale as the measured
                PSD. Falls back to the chunk's own median PSD if not supplied.

        Returns:
            The estimated CFO, in Hz, or None if no confident two-tone detection was found.
        """
        # LOCAL VARIABLES
        estim_cfo = None  # Estimated CFO (in Hz)

        # SETUP
        nperseg = min(self._nperseg, len(samples))
        freqs, psd = scipy.signal.welch(samples, fs=self._sample_rate,
                                         nperseg=nperseg, return_onesided=False)
        freqs = numpy.fft.fftshift(freqs)
        psd_db = 10 * numpy.log10(numpy.fft.fftshift(psd) + 1e-20)
        if noise_floor_db is None:
            noise_floor_db = numpy.median(psd_db)

        # MEASURE IT
        expected_f0, expected_f1 = -self._freq_sep / 2, self._freq_sep / 2
        mask0 = numpy.abs(freqs - expected_f0) <= self._tolerance_hz
        mask1 = numpy.abs(freqs - expected_f1) <= self._tolerance_hz
        peak0_idx = numpy.argmax(numpy.where(mask0, psd_db, -numpy.inf))
        peak1_idx = numpy.argmax(numpy.where(mask1, psd_db, -numpy.inf))

        snr0_db = psd_db[peak0_idx] - noise_floor_db
        snr1_db = psd_db[peak1_idx] - noise_floor_db
        if snr0_db >= self._snr_threshold_db and snr1_db >= self._snr_threshold_db:
            # Reject false pairs: A genuine detection has its two peaks freq_sep apart,
            # regardless of CFO (CFO shifts both tones equally, so the gap is CFO-invariant)
            peak0_freq, peak1_freq = freqs[peak0_idx], freqs[peak1_idx]
            measured_sep = peak1_freq - peak0_freq
            if abs(measured_sep - self._freq_sep) <= self._sep_tolerance_hz:
                estim_cfo = float(((peak0_freq - expected_f0) + (peak1_freq - expected_f1)) / 2)

        # DONE
        return estim_cfo
