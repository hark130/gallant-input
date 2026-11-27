"""Defines the BurstDetector class: find bursts of energy in a stream of complex samples.

Power envelope: |x|^2 smoothed by a moving average (default 64 samples = 16 symbols).
Noise floor:    the median power of the first train_len samples (nothing is detected
                while training), then slowly updated using only samples outside bursts.
Hysteresis:     a burst starts when power rises on_db above the floor and ends when it
                falls below off_db, so a brief dip mid-frame doesn't split it in two.
Output:         Burst(start, samples), where start is the absolute sample index in the
                stream.  Each burst includes pre_pad samples from before the detected
                start, because the moving average detects the start a little late.
Length limits:  bursts shorter than min_len are discarded; a burst that reaches max_len
                is forced closed, so a stuck interferer can't grow one burst forever.

Stateful: everything (filter state, noise floor, an open burst, pre-padding history) carries
across calls, so chunks of any size find the same bursts as one big call.
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

        # POWER ENVELOPE: a moving average of |x|^2, as an FIR filter so its state can carry
        # across chunks (the first window - 1 outputs ramp up from zero; training skips them)
        self._avg_taps = np.full(window, 1.0 / window)  # Equal weights = moving average
        self._avg_state = np.zeros(window - 1)          # Filter memory between chunks

        # THRESHOLDS: stored as linear power ratios, multiplied by the floor when used
        self._start_ratio = 10 ** (on_db / 10)  # Burst starts at floor * this
        self._stop_ratio = 10 ** (off_db / 10)  # Burst ends below floor * this
        self._min_len = min_len                 # Shortest burst kept
        self._max_len = max_len                 # Longest burst allowed

        # NOISE FLOOR: given (fixed), or trained on the first train_len samples, then tracked
        self._floor_is_fixed = noise_floor is not None  # Never update a given floor
        self._noise_floor = noise_floor                 # Linear noise power estimate
        self._floor_alpha = floor_alpha                 # Smoothing for each floor update
        self._train_len = train_len                     # Training length (samples)
        self._training_power = []                       # Power collected during training
        self._ramp_up_left = window - 1                 # Ramp-up outputs training must skip

        # STREAM POSITION AND PRE-PADDING
        self._pre_pad = 2 * window if pre_pad is None else pre_pad  # Kept before each start
        self._lookback = np.zeros(0, dtype=np.complex64)  # Most recent pre_pad samples seen
        self._stream_index = 0                            # Absolute index of the next sample

        # THE OPEN BURST (if any)
        self._in_burst = False    # A burst was still open at the end of the last chunk
        self._burst_pieces = []   # Its samples so far, one array per chunk it spans
        self._burst_len = 0       # Total samples in _burst_pieces
        self._burst_start = 0     # Absolute index of its first sample (pre-padding included)
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    @property
    def noise_floor(self) -> float | None:
        """Current linear noise power estimate (None until training finishes)."""
        return self._noise_floor

    def flush(self) -> list[Burst]:
        """Close any open burst (e.g., at the end of a capture file)."""
        bursts = []
        if self._in_burst:
            self._close_burst(bursts)
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
        bursts = []                                    # Completed bursts
        chunk = np.asarray(chunk, dtype=np.complex64)  # Normalized input
        power = None                                   # Smoothed power envelope
        active = None                                  # True where a burst is active
        trained = 0                                    # Samples consumed by training

        # INPUT VALIDATION
        if chunk.ndim != 1:
            raise ValueError(f"Expected a 1-D array, got shape {chunk.shape}")
        if chunk.size == 0:
            return bursts

        # POWER ENVELOPE
        power, self._avg_state = lfilter(self._avg_taps, 1.0, np.abs(chunk) ** 2,
                                         zi=self._avg_state)

        # TRAIN THE NOISE FLOOR FIRST (no detection until there's a floor to compare against)
        if self._noise_floor is None:
            trained = self._train_noise_floor(chunk, power)
            chunk, power = chunk[trained:], power[trained:]  # Detect on whatever is left
            if chunk.size == 0:
                return bursts

        # DETECT: which samples are inside a burst, then open/extend/close bursts to match
        active = self._burst_mask(power)
        self._track_bursts(chunk, active, bursts)

        # BOOKKEEPING FOR THE NEXT CHUNK
        self._track_noise_floor(power[~active])  # Only noise, never burst power
        self._lookback = _last_n(np.concatenate([self._lookback, chunk]), self._pre_pad)
        self._stream_index += chunk.size

        # DONE
        return bursts

    def _burst_mask(self, power: np.ndarray) -> np.ndarray:
        """Apply hysteresis: True where a burst is active.

        Each sample is an event: +1 (power at/above the start threshold: turn on), -1 (below
        the stop threshold: turn off), or 0 (in between: keep the previous state).  The state
        at each sample is the most recent nonzero event, or the state carried over from the
        last chunk if there hasn't been one yet.  Example, starting "off":

            events:  [ 0, +1,  0,  0, -1,  0]
            active:  [ F,  T,  T,  T,  F,  F]
        """
        # LOCAL VARIABLES
        events = np.zeros(power.size, dtype=np.int8)  # +1 = turn on, -1 = turn off, 0 = hold
        last_event_at = np.arange(power.size)         # Index of the most recent event
        carried_state = 1 if self._in_burst else -1   # State before this chunk, as an event

        # FIND EVENTS
        events[power >= self._noise_floor * self._start_ratio] = 1
        events[power < self._noise_floor * self._stop_ratio] = -1

        # HOLD THE LAST EVENT (vectorized "forward fill")
        # Mark non-events with -1, then a running maximum carries each event's index forward
        # until the next event: [-1, 1, -1, -1, 4, -1] -> [-1, 1, 1, 1, 4, 4].  -1 left at
        # the front means "no event yet in this chunk", so use the carried-over state.
        last_event_at[events == 0] = -1
        np.maximum.accumulate(last_event_at, out=last_event_at)
        return np.where(last_event_at >= 0, events[np.maximum(last_event_at, 0)],
                        carried_state) == 1

    def _track_bursts(self, chunk: np.ndarray, active: np.ndarray,
                      bursts: list[Burst]) -> None:
        """Open, extend, and close bursts to match the active mask."""
        # LOCAL VARIABLES
        before = np.array([self._in_burst], dtype=np.int8)  # State before this chunk
        # Differences between neighbors: +1 where a burst starts, -1 where one ends.  Putting
        # the carried-over state in front means a burst open since the last chunk can end here.
        transitions = np.diff(np.concatenate([before, active.astype(np.int8)]))
        segment_start = 0  # Where the open burst's samples in this chunk begin

        # WALK THE TRANSITIONS
        for edge in np.flatnonzero(transitions):
            if transitions[edge] == 1:
                self._open_burst(chunk, edge)
                segment_start = edge
            elif self._in_burst:  # (it may already be force-closed by max_len)
                self._extend_burst(chunk[segment_start:edge], bursts)
                if self._in_burst:
                    self._close_burst(bursts)
        if self._in_burst:
            self._extend_burst(chunk[segment_start:], bursts)  # Continues into the next chunk

    def _open_burst(self, chunk: np.ndarray, edge: int) -> None:
        """Open a burst at chunk[edge], starting it up to pre_pad samples earlier."""
        pre = _last_n(np.concatenate([self._lookback, chunk[:edge]]), self._pre_pad)
        self._burst_pieces = [pre]
        self._burst_len = pre.size
        self._burst_start = self._stream_index + edge - pre.size
        self._in_burst = True

    def _extend_burst(self, samples: np.ndarray, bursts: list[Burst]) -> None:
        """Add samples to the open burst, forcing it closed if it grows too long."""
        self._burst_pieces.append(samples)
        self._burst_len += samples.size
        if self._burst_len >= self._max_len:
            self._close_burst(bursts)  # Stuck above threshold (interference?); stop growing

    def _close_burst(self, bursts: list[Burst]) -> None:
        """Close the open burst, keeping it only if it's long enough."""
        if self._burst_len >= self._min_len:
            bursts.append(Burst(start=self._burst_start,
                                samples=np.concatenate(self._burst_pieces)))
        self._in_burst = False
        self._burst_pieces = []
        self._burst_len = 0

    def _train_noise_floor(self, chunk: np.ndarray, power: np.ndarray) -> int:
        """Collect power until train_len samples are in, then set the initial noise floor.

        Uses the median, not the mean: a burst during training barely moves it, as long as
        bursts occupy less than half of the training period.

        Returns:
            Number of samples from the front of chunk consumed by training.
        """
        used = min(chunk.size, self._train_len - self._stream_index)  # Samples still needed
        self._training_power.append(power[self._ramp_up_left:used])   # Skip filter ramp-up
        self._ramp_up_left = max(self._ramp_up_left - used, 0)
        self._lookback = _last_n(np.concatenate([self._lookback, chunk[:used]]), self._pre_pad)
        self._stream_index += used
        if self._stream_index >= self._train_len:
            trained = np.concatenate(self._training_power)
            self._noise_floor = max(float(np.median(trained)), MIN_NOISE_FLOOR)
            self._training_power = []
        return used

    def _track_noise_floor(self, idle_power: np.ndarray) -> None:
        """Nudge the noise floor toward the median power of this chunk's non-burst samples."""
        if self._floor_is_fixed or idle_power.size == 0:
            return
        estimate = float(np.median(idle_power))
        self._noise_floor = max((1 - self._floor_alpha) * self._noise_floor
                                + self._floor_alpha * estimate, MIN_NOISE_FLOOR)
    # pylint: enable=too-many-instance-attributes


def _last_n(samples: np.ndarray, num: int) -> np.ndarray:
    """The last num samples (written out because samples[-0:] returns everything)."""
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
