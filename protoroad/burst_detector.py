"""Defines the BurstDetector class.

Find bursts of energy in a stream of complex samples.

Power envelope: abs(x)^2 smoothed by a 64-sample moving average (16 symbols).
    The filter state carries across chunks, the same way your MatchedFilter does.
Noise floor: the first 8,192 samples (about 8 ms) are used for training.
    The detector takes the median power over that window and reports no bursts during it.
    After that, the floor is updated slowly, using only samples that are outside a burst.
Hysteresis: a burst starts when power rises 6 dB above the floor and ends when it falls below 3 dB.
    With two thresholds, a power dip in the middle of a frame doesn’t split it in two.
Output: a list of Burst(start, samples). start is the absolute sample index in the stream,
    which is handy when you’re cross-checking against a capture file.
    Each burst also includes 128 samples before the detected start,
    because the moving average detects the start slightly late.
Length limits: bursts shorter than min_len are discarded.
    A burst that reaches max_len is forced closed,
    so a stuck interferer can’t grow one burst forever.
"""

# Standard Imports
from dataclasses import dataclass
from typing import Final
# Third Party Imports
import numpy as np
from scipy.signal import lfilter
# Local Imports

DEFAULT_FLOOR_ALPHA: Final[float] = 0.05  # Noise floor smoothing; 0 = frozen, 1 = no memory
DEFAULT_MAX_LEN: Final[int] = 100_000     # Force a burst closed after this many samples
DEFAULT_MIN_LEN: Final[int] = 256         # Discard bursts shorter than this many samples
DEFAULT_OFF_DB: Final[float] = 3.0        # Burst ends when power drops below floor + this
DEFAULT_ON_DB: Final[float] = 6.0         # Burst starts when power rises above floor + this
DEFAULT_TRAIN_LEN: Final[int] = 8_192     # Samples used to estimate the initial noise floor
DEFAULT_WINDOW: Final[int] = 64           # Power averaging window (samples); 16 symbols @ 4 sps
MIN_NOISE_FLOOR: Final[float] = 1e-12     # Keeps the floor (and its thresholds) above zero


@dataclass
class Burst:
    """One detected burst."""

    start: int           # Absolute index of samples[0] in the stream (includes pre-padding)
    samples: np.ndarray  # Complex samples of the burst, complex64


class BurstDetector:
    """Detect bursts using smoothed power, an adaptive noise floor, and hysteresis.

    Stateful: feed it consecutive chunks of any size and it carries everything (filter state,
    noise floor, an open burst, pre-padding history) across chunk boundaries.  Feeding an
    entire capture as one chunk works too; see detect_bursts().
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    # pylint: disable=too-many-instance-attributes
    def __init__(self, window: int = DEFAULT_WINDOW, on_db: float = DEFAULT_ON_DB,
                 off_db: float = DEFAULT_OFF_DB, min_len: int = DEFAULT_MIN_LEN,
                 max_len: int = DEFAULT_MAX_LEN, noise_floor: float | None = None,
                 floor_alpha: float = DEFAULT_FLOOR_ALPHA, pre_pad: int | None = None,
                 train_len: int = DEFAULT_TRAIN_LEN):
        """Class ctor.

        Args:
            window: [OPTIONAL] Moving-average length (samples) for the power envelope.
            on_db: [OPTIONAL] Start threshold, dB above the noise floor.
            off_db: [OPTIONAL] Stop threshold, dB above the noise floor (must be <= on_db).
            min_len: [OPTIONAL] Bursts shorter than this (samples) are discarded.
            max_len: [OPTIONAL] Bursts are forced closed at this length (samples).
            noise_floor: [OPTIONAL] Fixed noise power (linear); None estimates and tracks it.
            floor_alpha: [OPTIONAL] Per-chunk smoothing factor for the noise floor estimate.
            pre_pad: [OPTIONAL] Samples kept before the detected start; defaults to 2 * window.
            train_len: [OPTIONAL] Samples of (mostly) noise used to estimate the initial floor.
                Nothing is detected during training.  Ignored if noise_floor is given.
        """
        # INPUT VALIDATION
        if window < 1:
            raise ValueError(f"window must be >= 1, got {window}")
        if off_db > on_db:
            raise ValueError(f"off_db ({off_db}) must be <= on_db ({on_db})")
        if train_len < window:
            raise ValueError(f"train_len ({train_len}) must be >= window ({window})")
        if not 0 < min_len <= max_len:
            raise ValueError(f"Need 0 < min_len <= max_len, got {min_len} and {max_len}")

        # LOCAL VARIABLES
        self._taps = np.full(window, 1.0 / window)                  # Moving-average taps
        self._zi = np.zeros(window - 1)                             # Moving-average filter state
        self._on_ratio = 10 ** (on_db / 10)                         # Linear start threshold ratio
        self._off_ratio = 10 ** (off_db / 10)                       # Linear stop threshold ratio
        self._min_len = min_len                                     # Shortest burst kept
        self._max_len = max_len                                     # Longest burst allowed
        self._fixed_floor = noise_floor is not None                 # Never update a given floor
        self._noise_floor = noise_floor                             # Linear noise power estimate
        self._floor_alpha = floor_alpha                             # Noise floor smoothing factor
        self._pre_pad = 2 * window if pre_pad is None else pre_pad  # Kept before start
        self._history = np.zeros(0, dtype=np.complex64)             # Tail of the previous chunk(s)
        self._count = 0                                             # Stream index of next chunk
        self._in_burst = False                                      # Burst open at last chunk end
        self._parts = []                                            # Pieces of the open burst
        self._burst_len = 0                                         # Samples in the open burst
        self._burst_start = 0                                       # Stream index of open burst
        self._skip = window - 1                                     # Filter start-up transient
        self._train_len = train_len                                 # Training length (samples)
        self._train = []                                            # Power collected in training
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    @property
    def noise_floor(self) -> float | None:
        """Current linear noise power estimate (None until the first chunk)."""
        return self._noise_floor

    def flush(self) -> list[Burst]:
        """Close any open burst (e.g., end of a capture file)."""
        bursts = []
        if self._in_burst:
            self._close(bursts)
        return bursts

    def process(self, chunk: np.ndarray) -> list[Burst]:
        """Process the next chunk of samples.

        Args:
            chunk: 1-D complex samples, contiguous with the previous chunk.

        Returns:
            Bursts that ended in this chunk (possibly empty).  A burst still in progress is
            returned by a later call, or by flush().
        """
        # LOCAL VARIABLES
        bursts = []                                       # Completed bursts
        chunk = np.asarray(chunk, dtype=np.complex64)     # Normalized input
        power = None                                      # Smoothed power envelope
        state = None                                      # True where a burst is active

        # INPUT VALIDATION
        if chunk.ndim != 1:
            raise ValueError(f"Expected a 1-D array, got shape {chunk.shape}")
        if chunk.size == 0:
            return bursts

        # DETECT IT
        power, self._zi = lfilter(self._taps, 1.0, np.abs(chunk) ** 2, zi=self._zi)
        if self._noise_floor is None:
            used = self._training(chunk, power)            # Samples consumed by training
            chunk, power = chunk[used:], power[used:]      # Detect on whatever is left
            if chunk.size == 0:
                return bursts
        state = self._hysteresis(power)
        self._collect(chunk, state, bursts)

        # BOOKKEEPING
        self._update_floor(power[~state])
        self._history = _tail(np.concatenate([self._history, chunk]), self._pre_pad)
        self._count += chunk.size

        # DONE
        return bursts

    def _append(self, samples: np.ndarray, bursts: list[Burst]) -> None:
        """Add samples to the open burst, forcing it closed if it grows too long."""
        self._parts.append(samples)
        self._burst_len += samples.size
        if self._burst_len >= self._max_len:
            self._close(bursts)  # Stuck above threshold (interference?); don't grow forever

    def _close(self, bursts: list[Burst]) -> None:
        """Close the open burst, keeping it if it's long enough."""
        if self._burst_len >= self._min_len:
            bursts.append(Burst(start=self._burst_start, samples=np.concatenate(self._parts)))
        self._in_burst = False
        self._parts = []
        self._burst_len = 0

    def _collect(self, chunk: np.ndarray, state: np.ndarray, bursts: list[Burst]) -> None:
        """Turn the state mask into opened, extended, and closed bursts."""
        # LOCAL VARIABLES
        prev = np.array([self._in_burst], dtype=np.int8)        # State before this chunk
        edges = np.diff(np.concatenate([prev, state.astype(np.int8)]))  # +1 rise, -1 fall
        seg_start = 0                                           # Start of the current segment

        # WALK THE EDGES
        for edge in np.flatnonzero(edges):
            if edges[edge] == 1:
                self._open(chunk, edge)
                seg_start = edge
            elif self._in_burst:  # May already be force-closed by max_len
                self._append(chunk[seg_start:edge], bursts)
                if self._in_burst:
                    self._close(bursts)
        if self._in_burst:
            self._append(chunk[seg_start:], bursts)  # Burst continues into the next chunk

    def _hysteresis(self, power: np.ndarray) -> np.ndarray:
        """Return True where a burst is active: on above the on-threshold, off below off."""
        # LOCAL VARIABLES
        events = np.zeros(power.size, dtype=np.int8)  # +1 = turn on, -1 = turn off, 0 = hold
        last = np.arange(power.size)                  # Index of the most recent event
        initial = 1 if self._in_burst else -1         # Carried-over state

        # FIND EVENTS
        events[power >= self._noise_floor * self._on_ratio] = 1
        events[power < self._noise_floor * self._off_ratio] = -1

        # HOLD THE LAST EVENT (vectorized forward fill)
        last[events == 0] = -1
        np.maximum.accumulate(last, out=last)
        return np.where(last >= 0, events[np.maximum(last, 0)], initial) == 1

    def _open(self, chunk: np.ndarray, edge: int) -> None:
        """Open a burst at chunk[edge], prepending up to pre_pad earlier samples."""
        pre = _tail(np.concatenate([self._history, chunk[:edge]]), self._pre_pad)
        self._parts = [pre]
        self._burst_len = pre.size
        self._burst_start = self._count + edge - pre.size
        self._in_burst = True

    def _training(self, chunk: np.ndarray, power: np.ndarray) -> int:
        """Collect power until train_len samples are in, then set the initial noise floor.

        Assumes bursts occupy less than half of the training period (median is robust to them).

        Returns:
            Number of samples from the front of chunk consumed by training.
        """
        used = min(chunk.size, self._train_len - self._count)  # Samples still needed
        self._train.append(power[self._skip:used])             # Drop the filter's ramp-up
        self._skip = max(self._skip - used, 0)
        self._history = _tail(np.concatenate([self._history, chunk[:used]]), self._pre_pad)
        self._count += used
        if self._count >= self._train_len:
            trained = np.concatenate(self._train)
            self._noise_floor = max(float(np.median(trained)), MIN_NOISE_FLOOR)
            self._train = []
        return used

    def _update_floor(self, idle_power: np.ndarray) -> None:
        """Track the noise floor using only samples outside bursts."""
        if self._fixed_floor or idle_power.size == 0:
            return
        estimate = float(np.median(idle_power))
        self._noise_floor = max((1 - self._floor_alpha) * self._noise_floor
                                + self._floor_alpha * estimate, MIN_NOISE_FLOOR)
    # pylint: enable=too-many-instance-attributes


def _tail(samples: np.ndarray, num: int) -> np.ndarray:
    """Last num samples (samples[-0:] would return everything, not nothing)."""
    return samples[samples.size - min(num, samples.size):]


def detect_bursts(samples: np.ndarray, **kwargs) -> list[Burst]:
    """Offline convenience: detect every burst in a whole capture.

    Example Usage:
        samples = np.fromfile("capture.c64", dtype=np.complex64)
        for burst in detect_bursts(samples, min_len=2_000):
            print(burst.start, len(burst.samples))

    Args:
        samples: 1-D complex samples (e.g., a GNU Radio File Sink capture).
        kwargs: Passed through to BurstDetector().
    """
    detector = BurstDetector(**kwargs)
    return detector.process(samples) + detector.flush()
