"""Defines the GardnerTimingRecovery class: symbol timing recovery for BPSK."""

# Standard Imports
from typing import Final
# Third Party Imports
import numpy as np
# Local Imports

DEFAULT_DAMPING: Final[float] = 0.707     # Loop damping factor (zeta); 1/sqrt(2) is the classic
DEFAULT_LOOP_BW: Final[float] = 0.02      # Loop noise bandwidth, normalized to the symbol rate;
                                          # 0.01 sometimes hangs up on a 64-symbol preamble
GARDNER_TED_GAIN: Final[float] = 0.265    # TED slope (per sample of timing error), measured for
                                          # RRC alpha=0.35, 4 sps, symbols at +/-1
_INTERP_BEFORE: Final[int] = 1            # Cubic interpolation needs 1 sample before index i...
_INTERP_AFTER: Final[int] = 2             # ...and 2 samples after it


class GardnerTimingRecovery:
    """Recover symbol timing from matched-filtered samples using a Gardner timing error detector.

    Classic closed-loop structure:
        1. Interpolator: cubic (Lagrange) interpolation at a fractional sample position
        2. Timing error detector (TED): Gardner, e = Re{ y*(k-1/2) * (y(k-1) - y(k)) }
        3. Loop filter: proportional-plus-integral (second-order loop)
        4. Controller: advance the fractional position by sps + loop filter output

    Gardner needs two samples per symbol (the symbol and the midpoint between symbols) and is
    insensitive to carrier phase, so it runs BEFORE carrier recovery.

    Stateful: process() carries the loop state and the samples the interpolator still needs
    across calls, so chunks of any size give the same symbols as one big call.  Two modes:
        - Streaming:  call process() on consecutive chunks; reset() only if the stream breaks.
        - Burst mode: call recover(burst), which is reset() + process(burst).

    The TED's gain scales with signal amplitude squared, so the loop gains assume the input's
    symbols are near +/-1 (i.e., AGC upstream).  A much weaker input makes the loop sluggish;
    a much stronger one makes it jittery or unstable.
    """

    def __init__(self, sps: int, loop_bw: float = DEFAULT_LOOP_BW,
                 damping: float = DEFAULT_DAMPING, ted_gain: float = GARDNER_TED_GAIN):
        """Class ctor.

        Args:
            sps: Samples per symbol of the input (must be >= 2; Gardner needs the midpoint).
            loop_bw: [OPTIONAL] Loop noise bandwidth (BnTs), normalized to the symbol rate.
                Wider locks faster but jitters more.
            damping: [OPTIONAL] Loop damping factor (zeta).
            ted_gain: [OPTIONAL] Slope of the TED's S-curve at the expected input amplitude;
                see GARDNER_TED_GAIN.
        """
        # INPUT VALIDATION
        if sps < 2:
            raise ValueError(f"Gardner timing recovery needs sps >= 2, got {sps}")
        if not 0 < loop_bw < 0.5:
            raise ValueError(f"loop_bw must be in (0, 0.5), got {loop_bw}")

        # LOCAL VARIABLES
        theta = loop_bw / (damping + 1 / (4 * damping))  # Standard 2nd-order loop design
        denom = 1 + 2 * damping * theta + theta ** 2      # Common denominator
        self._sps = sps                                       # Nominal samples per symbol
        self._half = sps / 2                                  # Midpoint offset (samples)
        self._kp = (4 * damping * theta / denom) / ted_gain  # Proportional gain
        self._ki = (4 * theta ** 2 / denom) / ted_gain       # Integral gain
        # Loop state (see reset())
        self._buffer = np.zeros(0, dtype=np.complex64)  # Unconsumed samples (+ history)
        self._index = 0                                 # Next symbol: integer index...
        self._mu = 0.0                                  # ...plus fractional offset [0, 1)
        self._integrator = 0.0                          # Loop filter integrator (rate error)
        self._prev = 0j                                 # Previous symbol
        self._dropped = 0                               # Samples discarded from _buffer so far
        self.last_offsets = np.zeros(0)  # DEBUG: absolute sample position of each symbol from
                                         # the most recent call (absolute since the last reset)
        self.reset()

    def process(self, samples: np.ndarray) -> np.ndarray:
        """Recover symbols from the next chunk of a matched-filtered stream.

        Args:
            samples: 1-D complex samples, contiguous with the previous chunk, already through
                the RX matched filter, with symbols near +/-1 in amplitude.

        Returns:
            1-D complex64 array of the symbols completed by this chunk (possibly empty).
            Carrier phase is untouched.
        """
        # LOCAL VARIABLES
        samples = np.asarray(samples, dtype=np.complex64)
        buffer = None  # Leftover samples + this chunk
        symbols = []   # Recovered symbols
        offsets = []   # DEBUG: absolute position of each symbol
        keep = 0       # First buffer index still needed after this call

        # INPUT VALIDATION
        if samples.ndim != 1:
            raise ValueError(f"Expected a 1-D array, got shape {samples.shape}")

        # RECOVER IT
        buffer = np.concatenate([self._buffer, samples])
        while self._index + _INTERP_AFTER < buffer.size:
            now = _interpolate(buffer, self._index, self._mu)
            mid = _interpolate(buffer, *_split(self._index, self._mu - self._half))
            error = (mid.real * (self._prev.real - now.real)
                     + mid.imag * (self._prev.imag - now.imag))  # Re{conj(mid) * (prev - now)}
            # Loop filter (PI), then advance to the next symbol
            self._integrator += self._ki * error
            symbols.append(now)
            offsets.append(self._dropped + self._index + self._mu)
            self._prev = now
            self._index, self._mu = _split(self._index,
                                           self._mu + self._sps + self._kp * error
                                           + self._integrator)

        # Only keep what the next symbol still needs (its midpoint reaches back half a symbol)
        keep = _split(self._index, self._mu - self._half)[0] - _INTERP_BEFORE
        keep = min(max(keep, 0), buffer.size)
        self._buffer = buffer[keep:]
        self._index -= keep  # Integer shift: exact, so chunking can't change the result
        self._dropped += keep

        # DONE
        self.last_offsets = np.asarray(offsets)
        return np.asarray(symbols, dtype=np.complex64)

    def recover(self, burst: np.ndarray) -> np.ndarray:
        """Burst mode: reset the loop, then recover every symbol in one complete burst."""
        self.reset()
        return self.process(burst)

    def reset(self) -> None:
        """Return the loop to its initial state (e.g., at the start of a new burst)."""
        self._buffer = np.zeros(0, dtype=np.complex64)
        self._index = self._sps  # First symbol: far enough in for its midpoint + history
        self._mu = 0.0
        self._integrator = 0.0
        self._prev = 0j
        self._dropped = 0


def _interpolate(samples: np.ndarray, i: int, mu: float) -> complex:
    """Cubic Lagrange interpolation of samples at index i + mu (needs i >= 1, 0 <= mu < 1)."""
    x_m1, x_0, x_1, x_2 = samples[i - 1], samples[i], samples[i + 1], samples[i + 2]
    return (x_m1 * (-mu * (mu - 1) * (mu - 2) / 6)
            + x_0 * ((mu + 1) * (mu - 1) * (mu - 2) / 2)
            + x_1 * (-(mu + 1) * mu * (mu - 2) / 2)
            + x_2 * ((mu + 1) * mu * (mu - 1) / 6))


def _split(index: int, offset: float) -> tuple[int, float]:
    """Normalize index + offset into (integer index, fractional offset in [0, 1))."""
    whole = int(np.floor(offset))
    return index + whole, offset - whole
