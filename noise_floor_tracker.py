"""Defines the NoiseFloorTracker class: estimate, then track, the noise floor of a stream."""

# Standard Imports
from typing import Final, List
# Third Party Imports
import numpy as np
# Local Imports

MIN_NOISE_FLOOR: Final[float] = 1e-12  # Keeps the floor (and thresholds built on it) above zero


class NoiseFloorTracker:
    """Estimate, then track, the noise floor of a stream (linear magnitude).

    Training: the median of the first train_len samples becomes the initial floor.  The median
        tolerates bursts in the training data, as long as they cover less than half of it.
    Tracking: each later batch nudges the floor toward the batch mean, using an exponential
        moving average (EMA).  The caller must only pass samples it classified as noise.

    Stateful: feed it consecutive batches of any size.  The adaptation rate (alpha) is defined
    per sample, so the floor adapts at the same rate regardless of batch size.
    """

    def __init__(self, train_len: int, alpha: float, train_percentile: float = 50.0):
        """Class ctor.

        Args:
            train_len: Number of samples used to estimate the initial floor.
            alpha: Per-sample EMA weight for tracking, in (0, 1].  Smaller adapts slower; the
                floor's time constant is roughly 1 / alpha samples.
            train_percentile: [OPTIONAL] Percentile of the training samples used as the initial
                floor.  The default (50, the median) assumes bursts fill less than half of the
                training window; lower it for a busy band (e.g., 10 tolerates 90% busy).

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # INPUT VALIDATION
        if not isinstance(train_len, int) or isinstance(train_len, bool):
            raise TypeError(f"train_len must be an int, got {type(train_len)}")
        if train_len < 1:
            raise ValueError(f"train_len must be >= 1, got {train_len}")
        if not isinstance(alpha, (int, float)) or isinstance(alpha, bool):
            raise TypeError(f"alpha must be a float, got {type(alpha)}")
        if not 0 < alpha <= 1:
            raise ValueError(f"alpha must be in (0, 1], got {alpha}")
        if not 0 < train_percentile < 100:
            raise ValueError(f"train_percentile must be in (0, 100), got {train_percentile}")

        # ATTRIBUTES
        self._train_len: int = train_len                  # Samples needed to finish training
        self._alpha: float = float(alpha)                 # Per-sample EMA weight
        self._floor: float | None = None                  # Linear floor estimate (None = training)
        self._training: List[np.ndarray] = []             # Training samples collected so far
        self._num_trained: int = 0                        # Total samples in _training
        self._train_percentile: float = train_percentile  # Initial floor's percentile

    def get_floor(self) -> float | None:
        """Return the current linear floor estimate, or None while still training."""
        return self._floor

    def get_train_remaining(self) -> int:
        """Return how many more samples training needs (0 once trained)."""
        return self._train_len - self._num_trained

    def update(self, noise_env: np.ndarray) -> None:
        """Fold envelope samples the caller classified as noise into the estimate.

        Args:
            noise_env: 1-D array of linear envelope (magnitude) samples.  May be empty (e.g., a
                chunk that was entirely inside a burst), which changes nothing.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        remaining = noise_env  # Samples not yet consumed by training

        # INPUT VALIDATION
        if not isinstance(noise_env, np.ndarray):
            raise TypeError(f"noise_env must be a numpy.ndarray, got {type(noise_env)}")
        if noise_env.ndim != 1:
            raise ValueError(f"noise_env must be 1-D, got {noise_env.ndim} dimensions")
        if np.iscomplexobj(noise_env):
            raise TypeError("noise_env must be real (pass the envelope, not the IQ samples)")

        # UPDATE IT
        if self._floor is None:
            remaining = self._train_floor(noise_env)
        if self._floor is not None and remaining.size > 0:
            self._track_floor(remaining)

    def _train_floor(self, noise_env: np.ndarray) -> np.ndarray:
        """Collect training samples; set the initial floor once there are enough.

        Returns:
            The samples training didn't need, for tracking (possibly empty).
        """
        # LOCAL VARIABLES
        needed = self._train_len - self._num_trained  # Samples training still needs
        taken = noise_env[:needed]                    # Samples consumed by training
        leftover = noise_env[needed:]                 # Samples left over for tracking

        # TRAIN IT
        self._training.append(taken)
        self._num_trained += taken.size
        if self._num_trained >= self._train_len:
            training = np.concatenate(self._training)  # Every training sample
            self._floor = max(float(np.percentile(training, self._train_percentile)),
                              MIN_NOISE_FLOOR)
            self._training = []  # Free the memory; training is done

        # DONE
        return leftover

    def _track_floor(self, noise_env: np.ndarray) -> None:
        """Nudge the floor toward the batch mean with a per-sample EMA weight."""
        # LOCAL VARIABLES
        weight = 1 - (1 - self._alpha) ** noise_env.size  # Batch weight == n per-sample steps
        batch_mean = float(np.mean(noise_env))            # Batch estimate of the floor

        # TRACK IT
        self._floor = max((1 - weight) * self._floor + weight * batch_mean, MIN_NOISE_FLOOR)
