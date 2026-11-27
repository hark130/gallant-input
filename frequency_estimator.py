"""Estimate the frequency offset of a burst: a plug-in interface plus two implementations.

FrequencyEstimator:         The interface.  Give it complex baseband samples and the sample
                            rate; get back the burst's offset (Hz) from the capture's center.
PeakFrequencyEstimator:     The frequency of the strongest bin.  Simple, but biased for FSK
                            (it lands on one tone instead of the carrier between them).
CentroidFrequencyEstimator: The power-weighted mean frequency of the strongest signal
                            region.  Lands between FSK tones (on the carrier) and holds up
                            at low SNR.

Both implementations share the same power spectrum: a Welch average (several Hann-windowed
FFTs, averaged) taken from the middle of the burst, which skips ramp-up/ramp-down at the edges.

Stateless: an estimator holds only its settings, so one instance can serve every burst,
channel, or thread.
"""

# Standard Imports
from abc import ABC, abstractmethod
from typing import Final, Tuple
# Third Party Imports
import numpy as np
# Local Imports

DEFAULT_FFT_LEN: Final[int] = 4096    # Samples per FFT; bin width = samp_rate / fft_len
DEFAULT_MASK_DB: Final[float] = 6.0   # Signal bins are at least this far above the noise
DEFAULT_MAX_SEGMENTS: Final[int] = 8  # Most FFTs averaged per burst (caps cost on long bursts)
MIN_FFT_LEN: Final[int] = 16          # Smallest FFT length accepted


class FrequencyEstimator(ABC):
    """Interface: estimate a burst's frequency offset from the capture's center frequency."""

    def __init__(self, fft_len: int = DEFAULT_FFT_LEN,
                 max_segments: int = DEFAULT_MAX_SEGMENTS):
        """Class ctor.

        Args:
            fft_len: [OPTIONAL] Samples per FFT.  Only needs to resolve the channel spacing;
                larger is finer (bin width = samp_rate / fft_len) but slower.
            max_segments: [OPTIONAL] Most FFTs averaged per burst.  More averaging lowers the
                noise in the spectrum estimate; fewer is faster.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # INPUT VALIDATION
        _validate_int(fft_len, "fft_len", MIN_FFT_LEN)
        _validate_int(max_segments, "max_segments", 1)

        # ATTRIBUTES
        self._fft_len: int = fft_len                    # Samples per FFT
        self._max_segments: int = max_segments          # Most FFTs averaged per burst
        self._window: np.ndarray = np.hanning(fft_len)  # Hann window: lowers spectral leakage

    def estimate(self, samples: np.ndarray, samp_rate: float) -> float:
        """Estimate the burst's frequency offset (Hz) from the capture's center frequency.

        Args:
            samples: 1-D complex baseband samples of one burst.
            samp_rate: Sample rate (samples per second).

        Returns:
            The estimated offset in Hz, in [-samp_rate / 2, samp_rate / 2).

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        freqs = None  # Frequency of each bin (Hz), DC centered
        power = None  # Averaged power of each bin, DC centered

        # INPUT VALIDATION
        _validate_samples(samples)
        if not isinstance(samp_rate, (int, float)) or isinstance(samp_rate, bool):
            raise TypeError(f"samp_rate must be a float, got {type(samp_rate)}")
        if samp_rate <= 0:
            raise ValueError(f"samp_rate must be > 0, got {samp_rate}")

        # ESTIMATE IT
        freqs, power = self._compute_power_spectrum(samples, samp_rate)

        # DONE
        return self._estimate_from_spectrum(freqs, power)

    @abstractmethod
    def _estimate_from_spectrum(self, freqs: np.ndarray, power: np.ndarray) -> float:
        """Reduce a DC-centered power spectrum to one frequency offset (Hz)."""

    def _compute_power_spectrum(self, samples: np.ndarray,
                                samp_rate: float) -> Tuple[np.ndarray, np.ndarray]:
        """Return (bin frequencies, Welch-averaged power), both DC centered.

        Uses up to max_segments non-overlapping segments from the middle of the burst.  A burst
        shorter than fft_len is zero-padded into a single segment.
        """
        # LOCAL VARIABLES
        num_seg = min(self._max_segments, max(1, samples.size // self._fft_len))  # FFTs used
        used = num_seg * self._fft_len                                            # Samples used
        first = max(0, (samples.size - used) // 2)                                # Middle start
        segments = None                                                           # 2-D segments
        spectra = None                                                            # FFT per row
        freqs = None                                                              # Bin centers
        power = None                                                              # Mean power

        # COMPUTE IT
        segments = np.zeros((num_seg, self._fft_len), dtype=np.complex128)
        segments.flat[:min(used, samples.size)] = samples[first:first + used]
        spectra = np.fft.fft(segments * self._window, axis=1)
        power = np.fft.fftshift(np.mean(np.abs(spectra) ** 2, axis=0))
        freqs = np.fft.fftshift(np.fft.fftfreq(self._fft_len, d=1 / samp_rate))

        # DONE
        return freqs, power


class PeakFrequencyEstimator(FrequencyEstimator):
    """The frequency of the strongest bin.  Biased by about +/- the deviation for FSK."""

    def _estimate_from_spectrum(self, freqs: np.ndarray, power: np.ndarray) -> float:
        """Return the frequency of the strongest bin."""
        return float(freqs[np.argmax(power)])


class CentroidFrequencyEstimator(FrequencyEstimator):
    """The power-weighted mean frequency of the strongest signal region.

    Signal bins are those at least mask_db above the noise, estimated as the median bin power
    (one hop occupies far less than half of a wideband capture, so most bins are noise).
    Contiguous signal bins form regions; the region with the most total power wins, so another
    emitter (or a narrow spur, whose single bin can out-peak a wide signal) can't pull the
    estimate toward itself.  If no bin clears the mask, the strongest bin is used instead.

    For FSK, the centroid is the carrier only when the tones are used equally often: an
    unbalanced bit pattern pulls it toward the busier tone (by up to the deviation).
    """

    def __init__(self, fft_len: int = DEFAULT_FFT_LEN,
                 max_segments: int = DEFAULT_MAX_SEGMENTS, mask_db: float = DEFAULT_MASK_DB):
        """Class ctor.

        Args:
            fft_len: [OPTIONAL] See FrequencyEstimator.
            max_segments: [OPTIONAL] See FrequencyEstimator.
            mask_db: [OPTIONAL] Signal bins are at least this many dB above the median bin.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        super().__init__(fft_len=fft_len, max_segments=max_segments)
        if not isinstance(mask_db, (int, float)) or isinstance(mask_db, bool):
            raise TypeError(f"mask_db must be a float, got {type(mask_db)}")
        if mask_db < 0:
            raise ValueError(f"mask_db must be >= 0, got {mask_db}")
        self._mask_ratio: float = 10 ** (mask_db / 10)  # Power ratio (power, so 10, not 20)

    def _estimate_from_spectrum(self, freqs: np.ndarray, power: np.ndarray) -> float:
        """Return the power-weighted mean frequency of the strongest signal region."""
        # LOCAL VARIABLES
        above = power > np.median(power) * self._mask_ratio      # True for signal bins
        bounded = np.concatenate(([0], above, [0])).astype(int)  # Mask, 0 at both ends
        edges = np.diff(bounded)                                 # +1 into a region, -1 out
        starts = np.flatnonzero(edges == 1)                      # First bin of each region
        stops = np.flatnonzero(edges == -1)                      # One past each region
        running = np.concatenate(([0.0], np.cumsum(power)))      # Running total of bin power
        totals = None                                            # Total power per region
        best = 0                                                 # Index of strongest region
        estimate = float(freqs[np.argmax(power)])                # Fallback: strongest bin

        # ESTIMATE IT
        if starts.size > 0:
            totals = running[stops] - running[starts]
            best = int(np.argmax(totals))
            estimate = float(np.average(freqs[starts[best]:stops[best]],
                                        weights=power[starts[best]:stops[best]]))

        # DONE
        return estimate


def _validate_int(value: int, name: str, minimum: int) -> None:
    """Validate an int argument on behalf of this module."""
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{name} must be an int, got {type(value)}")
    if value < minimum:
        raise ValueError(f"{name} must be >= {minimum}, got {value}")


def _validate_samples(samples: np.ndarray) -> None:
    """Validate burst samples on behalf of this module."""
    if not isinstance(samples, np.ndarray):
        raise TypeError(f"samples must be a numpy.ndarray, got {type(samples)}")
    if samples.ndim != 1 or samples.size == 0:
        raise ValueError(f"samples must be 1-D and non-empty, got shape {samples.shape}")
    if not np.iscomplexobj(samples):
        raise TypeError("samples must be complex baseband (IQ) samples")
