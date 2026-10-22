"""Defines the AGC class: automatic gain control for complex baseband samples."""

# Standard Imports
from typing import Final
# Third Party Imports
import numpy as np
# Local Imports

DEFAULT_ATTACK: Final[float] = 0.9      # Fraction (in dB) of the error removed per block when
                                        # the signal is too loud: fast, so bursts settle quickly
DEFAULT_BLOCK_LEN: Final[int] = 32      # Samples per gain update (8 symbols @ 4 sps)
DEFAULT_DECAY: Final[float] = 0.05      # Same, when the signal is too quiet: slow, so the gain
                                        # doesn't race up on noise between bursts
DEFAULT_MAX_GAIN: Final[float] = 1e6    # Gain ceiling (linear): +120 dB
DEFAULT_TARGET_RMS: Final[float] = 1.0  # Output RMS.  1.0 suits a matched-filter OUTPUT with
                                        # unit-energy RRC taps (symbols land near +/-1)
_MIN_POWER: Final[float] = 1e-30        # Below this a block is treated as silence


class AGC:
    """Normalize signal amplitude to a target RMS level.

    Two modes, matching the rest of the receiver:
        - Burst mode (block AGC):     normalize(burst) measures the burst's RMS once and scales
                                      the whole burst to the target.
        - Streaming (feedback AGC):   process(chunk) applies the current gain, measures the
                                      output power every block_len samples, and moves the gain
                                      toward the target in the dB domain.  The gain and the
                                      partially measured block carry across calls, so chunks of
                                      any size give the same output as one big call.
                                      Pass hold=True between bursts (AGC hold): otherwise the
                                      gain climbs on noise, and the next burst arrives far too
                                      loud for the loops downstream.

    The target RMS depends on where the AGC sits in the chain; see DEFAULT_TARGET_RMS.
    """

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, target_rms: float = DEFAULT_TARGET_RMS,
                 block_len: int = DEFAULT_BLOCK_LEN, attack: float = DEFAULT_ATTACK,
                 decay: float = DEFAULT_DECAY, max_gain: float = DEFAULT_MAX_GAIN,
                 initial_gain: float = 1.0):
        """Class ctor.

        Args:
            target_rms: [OPTIONAL] Desired output RMS amplitude.
            block_len: [OPTIONAL] Streaming: samples per gain update.
            attack: [OPTIONAL] Streaming: fraction (0, 1] of the dB error removed per block
                when the output is above target.  1.0 = jump straight to the target.
            decay: [OPTIONAL] Streaming: same, when the output is below target.
            max_gain: [OPTIONAL] Streaming: gain ceiling, so silence can't drive it to infinity.
            initial_gain: [OPTIONAL] Streaming: gain after reset().
        """
        # INPUT VALIDATION
        if target_rms <= 0:
            raise ValueError(f"target_rms must be > 0, got {target_rms}")
        if block_len < 1:
            raise ValueError(f"block_len must be >= 1, got {block_len}")
        for name, rate in (("attack", attack), ("decay", decay)):
            if not 0 < rate <= 1:
                raise ValueError(f"{name} must be in (0, 1], got {rate}")
        if not 0 < initial_gain <= max_gain:
            raise ValueError(f"Need 0 < initial_gain <= max_gain, got {initial_gain}, {max_gain}")

        # LOCAL VARIABLES
        self._target_power = target_rms ** 2  # Desired mean |y|^2
        self._block_len = block_len           # Samples per gain update
        self._attack = attack                 # Rate when too loud
        self._decay = decay                   # Rate when too quiet
        self._max_gain = max_gain             # Gain ceiling
        self._initial_gain = initial_gain     # Gain after reset()
        # Streaming state (see reset())
        self._gain = initial_gain             # Current linear gain
        self._block = []                      # Output samples of the current, unfinished block
        self._block_fill = 0                  # Samples in the current block
        self.reset()
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    @property
    def gain(self) -> float:
        """Current linear gain (streaming), or the gain the last normalize() applied."""
        return self._gain

    def normalize(self, burst: np.ndarray) -> np.ndarray:
        """Burst mode (block AGC): scale a whole burst so its RMS equals the target.

        Args:
            burst: 1-D complex samples of one complete burst.

        Returns:
            The scaled burst, complex64.  An all-zero burst is returned unchanged.
        """
        # LOCAL VARIABLES
        burst = np.asarray(burst, dtype=np.complex64)
        power = 0.0  # Mean |x|^2 of the burst

        # INPUT VALIDATION
        if burst.ndim != 1:
            raise ValueError(f"Expected a 1-D array, got shape {burst.shape}")

        # SCALE IT
        power = float(np.mean(np.abs(burst) ** 2)) if burst.size else 0.0
        if power < _MIN_POWER:
            return burst
        self._gain = float(np.sqrt(self._target_power / power))

        # DONE
        return (burst * self._gain).astype(np.complex64)

    def process(self, chunk: np.ndarray, hold: bool = False) -> np.ndarray:
        """Streaming (feedback AGC): apply and update the gain over the next chunk.

        Args:
            chunk: 1-D complex samples, contiguous with the previous chunk.
            hold: [OPTIONAL] If True, apply the current gain without updating it (AGC hold),
                e.g., while the burst detector says no burst is present.

        Returns:
            The gain-adjusted chunk, complex64.  Every sample in a block uses the gain that
            was current when the block started.
        """
        # LOCAL VARIABLES
        chunk = np.asarray(chunk, dtype=np.complex64)
        output = np.empty_like(chunk)  # Gain-adjusted samples
        start = 0                      # Start of the current segment of chunk
        stop = 0                       # End of the current segment (a block boundary or the end)

        # INPUT VALIDATION
        if chunk.ndim != 1:
            raise ValueError(f"Expected a 1-D array, got shape {chunk.shape}")

        # ADJUST IT, one block-aligned segment at a time
        while start < chunk.size:
            stop = min(start + self._block_len - self._block_fill, chunk.size)
            output[start:stop] = chunk[start:stop] * self._gain
            self._block.append(output[start:stop])
            self._block_fill += stop - start
            if self._block_fill == self._block_len:
                # Measure the whole block at once, so chunk boundaries can't change the result
                block = np.concatenate(self._block)
                if not hold:
                    self._update_gain(float(np.mean(np.abs(block) ** 2)))
                self._block = []
                self._block_fill = 0
            start = stop

        # DONE
        return output

    def reset(self) -> None:
        """Return the streaming state to its initial values."""
        self._gain = self._initial_gain
        self._block = []
        self._block_fill = 0

    def _update_gain(self, power: float) -> None:
        """First-order loop in dB: remove a fraction of the error between output and target."""
        if power < _MIN_POWER:
            ratio = self._max_gain / self._gain    # Silence: head for the ceiling (slowly)
            rate = self._decay
        else:
            ratio = np.sqrt(self._target_power / power)  # Gain change that would hit target
            rate = self._attack if ratio < 1 else self._decay
        self._gain = min(float(self._gain * ratio ** rate), self._max_gain)
