"""PoC burst detector (stand-in imports for local testing)."""

# Standard Imports
from enum import Enum
from typing import List, NamedTuple
# Third Party Imports
import numpy as np
# Local Imports
from noise_floor_tracker import NoiseFloorTracker


def compute_magnitude_spectrum(samples: np.ndarray) -> np.ndarray:
    """Stand-in for gallant_input.signal.compute_magnitude_spectrum()."""
    return np.absolute(samples)


class State(Enum):
    """Burst detector states."""

    IDLE = 0
    BURST = 1


class Burst(NamedTuple):
    """One burst: the half-open interval [start, stop) of absolute sample indices."""

    start: int
    stop: int


class BurstDetector:
    """Detect bursts with a smoothed envelope, an adaptive noise floor, and hysteresis."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, floor_tracker: NoiseFloorTracker, on_db: float, off_db: float,
                 window: int, min_len: int = 1):
        """Class ctor.

        Args:
            floor_tracker: Estimates, then tracks, the noise floor (linear magnitude).
            on_db: A burst starts when the smoothed envelope rises this many dB above the floor.
            off_db: A burst stops when the smoothed envelope falls below this many dB above the
                floor.  Must be <= on_db.
            window: Moving-average length (samples) used to smooth the envelope.
            min_len: [OPTIONAL] Bursts shorter than this (samples) are discarded.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # INPUT VALIDATION
        if not isinstance(floor_tracker, NoiseFloorTracker):
            raise TypeError(f"floor_tracker must be a NoiseFloorTracker, got {type(floor_tracker)}")
        if off_db > on_db:
            raise ValueError(f"off_db ({off_db}) must be <= on_db ({on_db})")
        if window < 1:
            raise ValueError(f"window must be >= 1, got {window}")
        if min_len < 1:
            raise ValueError(f"min_len must be >= 1, got {min_len}")

        # CONSTRUCT IT
        self._abs_index: int = -1        # Absolute index of the current sample
        self._bursts: List[Burst] = []   # List of Burst NamedTuples
        self._state: State = State.IDLE  # Current state
        self._abs_start: int = 0         # Absolute index of a burst start
        self._abs_stop: int = 0          # Absolute index of a burst stop (exclusive)
        self._min_len: int = min_len     # Shortest burst kept (samples)

        # Thresholds are relative to a tracked noise floor, stored as linear magnitude ratios
        self._floor_tracker: NoiseFloorTracker = floor_tracker  # Estimates the noise floor
        self._on_ratio: float = 10 ** (on_db / 20)              # Start: envelope > floor * this
        self._off_ratio: float = 10 ** (off_db / 20)            # Stop: envelope < floor * this

        # Detect bursts within a window to smooth out brief dips in amplitude
        self._window: int = window                           # Moving-average length (samples)
        self._kernel: np.ndarray = np.ones(window) / window  # Equal weights = moving average
        self._history: np.ndarray = np.zeros(window - 1)     # Last window - 1 magnitudes seen
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def detect_chunk(self, chunk: np.ndarray) -> None:
        """Detect the start and stop index of bursts from a chunk."""
        # LOCAL VARIABLES
        envelope = self._smooth_envelope(chunk)                                    # Smoothed mag
        num_train = min(self._floor_tracker.get_train_remaining(), envelope.size)  # Still training
        detect_env = envelope[num_train:]                                          # Scan these
        idle = None                                                                # Idle mask

        # TRAIN IT (the floor must exist before anything can be detected)
        if num_train > 0:
            self._abs_index += num_train
            self._floor_tracker.update(envelope[:num_train])

        # DETECT IT
        if detect_env.size > 0:
            idle = self._run_state_machine(envelope=detect_env,
                                           floor=self._floor_tracker.get_floor())
            self._floor_tracker.update(detect_env[idle])  # Only noise feeds the floor

    def flush(self) -> None:
        """Close a burst still open at the end of the stream (e.g., end of a capture file)."""
        if self._state is State.BURST:
            self._abs_stop = self._abs_index + 1  # Exclusive: one past the last sample seen
            self._process_burst()

    def get_bursts(self) -> List[Burst]:
        """Fetch all detected Bursts."""
        return list(self._bursts)

    def _process_burst(self) -> None:
        """Add a Burst to the _bursts list, if it's long enough, and reset."""
        if self._abs_stop - self._abs_start >= self._min_len:
            self._bursts.append(Burst(start=self._abs_start, stop=self._abs_stop))
        self._reset()

    def _reset(self) -> None:
        """Reset the state machine."""
        self._abs_start = 0
        self._abs_stop = 0
        self._state = State.IDLE

    def _run_state_machine(self, envelope: np.ndarray, floor: float) -> np.ndarray:
        """Open and close bursts, sample by sample, using hysteresis around the noise floor.

        Args:
            envelope: Smoothed linear magnitude, one value per sample.
            floor: Current linear noise floor.

        Returns:
            A boolean mask, the same length as envelope: True where no burst was open.
        """
        # LOCAL VARIABLES
        on_thresh = floor * self._on_ratio          # Envelope above this starts a burst
        off_thresh = floor * self._off_ratio        # Envelope below this stops a burst
        idle = np.zeros(envelope.size, dtype=bool)  # True where no burst was open

        # DETECT IT
        for index, value in enumerate(envelope):
            self._abs_index += 1
            if self._state is State.IDLE and value > on_thresh:
                self._abs_start = self._abs_index
                self._state = State.BURST
            elif self._state is State.BURST and value < off_thresh:
                self._abs_stop = self._abs_index  # Exclusive: first sample after the burst
                self._process_burst()
            idle[index] = self._state is State.IDLE

        # DONE
        return idle

    def _smooth_envelope(self, chunk: np.ndarray) -> np.ndarray:
        """Return the moving-average magnitude of chunk, continuous across chunks."""
        # LOCAL VARIABLES
        mag = compute_magnitude_spectrum(chunk)        # Magnitude of each sample
        padded = np.concatenate((self._history, mag))  # Prepend the previous chunk's tail
        envelope = None                                # Smoothed magnitude, len(chunk)

        # SMOOTH IT
        envelope = np.convolve(padded, self._kernel, mode="valid")
        self._history = padded[len(padded) - (self._window - 1):]  # Keep tail for next chunk

        # DONE
        return envelope
