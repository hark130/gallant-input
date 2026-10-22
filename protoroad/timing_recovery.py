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
MAX_RATE_CORRECTION: Final[float] = 0.25  # Max clock-rate correction (samples per symbol)
_SAMPLES_BEFORE: Final[int] = 1           # Cubic interpolation at index n + frac reads
_SAMPLES_AFTER: Final[int] = 2            # samples n-1, n, n+1, and n+2


class GardnerTimingRecovery:
    """Recover symbol timing from matched-filtered samples using a Gardner timing error detector.

    Classic closed-loop structure, run once per symbol:
        1. Interpolator: read the signal at a fractional sample position (cubic Lagrange)
        2. Timing error detector (TED): Gardner, e = Re{ y*(k-1/2) * (y(k-1) - y(k)) }
        3. Loop filter: proportional-plus-integral (second-order loop)
        4. Controller: next position = this position + sps + loop filter output

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

        # LOOP FILTER GAINS
        # Textbook second-order loop design: pick the loop's noise bandwidth and damping, and
        # these formulas give the proportional and integral gains.  Dividing by the TED gain
        # turns "timing error the TED reports" back into "samples of timing error."
        theta = loop_bw / (damping + 1 / (4 * damping))  # Normalized natural frequency
        denom = 1 + 2 * damping * theta + theta ** 2     # Shared denominator
        self._gain_prop = (4 * damping * theta / denom) / ted_gain  # Proportional (kp): fix offset
        self._gain_int = (4 * theta ** 2 / denom) / ted_gain        # Integral (ki)s: track drift

        # CONSTANTS
        self._sps = sps                         # Nominal samples per symbol
        self._half_symbol = sps / 2             # Distance from a symbol to its midpoint
        self._max_step_correction = sps / 2     # Never move more than half a symbol per symbol
        self._max_rate_correction = MAX_RATE_CORRECTION

        # LOOP STATE (initialized by reset())
        # Samples kept for the next call
        self._carryover = np.zeros(0, dtype=np.complex64)
        self._next_index = 0         # Next symbol's position: integer sample index into...
        self._next_frac = 0.0        # ...self._carryover, plus a fraction [0, 1) ("mu")
        self._rate_correction = 0.0  # Integrator: clock-rate mismatch (samples per symbol)
        self._prev_symbol = 0j       # The TED compares each symbol to the one before it
        self._discarded = 0          # Samples dropped since reset(); maps positions to absolute

        # DEBUG: absolute sample position of each symbol from the most recent call
        # (absolute since the last reset)
        self.last_offsets = np.zeros(0)
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
        signal = None     # Carryover from the last call + this chunk
        symbols = []      # Recovered symbols
        positions = []    # DEBUG: absolute sample position of each symbol
        first_needed = 0  # Earliest sample the next symbol still needs

        # INPUT VALIDATION
        if samples.ndim != 1:
            raise ValueError(f"Expected a 1-D array, got shape {samples.shape}")

        # RECOVER SYMBOLS (one loop iteration per symbol)
        #
        #    prev symbol         midpoint          this symbol
        #        |                   |                   |
        #   -----*---------+---------*---------+---------*-----> sample index
        #     y(k-1)             y(k-1/2)              y(k)
        #        |<------------- sps samples ----------->|
        #
        signal = np.concatenate([self._carryover, samples])
        while self._next_index + _SAMPLES_AFTER < signal.size:
            # 1. INTERPOLATOR: read the signal at this symbol and at the midpoint before it
            symbol = _interpolate_cubic(signal, self._next_index, self._next_frac)
            midpoint = _interpolate_cubic(signal, *_normalize_position(
                self._next_index, self._next_frac - self._half_symbol))

            # 2. TIMING ERROR DETECTOR (Gardner): Re{ conj(midpoint) * (prev - this) }
            # On a +1 -> -1 transition, (prev - this) is +2, and a correctly timed midpoint
            # sits on the zero crossing, so the error is 0.  Sampling late puts the midpoint
            # past the crossing (negative), so the error goes negative; early goes positive.
            # No transition (prev == this) means no timing information: the error is 0.
            # That's why the preamble alternates 1010...: a transition every symbol.
            timing_error = (midpoint.real * (self._prev_symbol.real - symbol.real)
                            + midpoint.imag * (self._prev_symbol.imag - symbol.imag))

            # 3. LOOP FILTER (proportional + integral), both clamped so one wild error (e.g.,
            # an input far too loud) can't run the loop backward or off the rails.
            # Integral: accumulates persistent error, e.g., the TX/RX clock-rate mismatch.
            self._rate_correction = float(np.clip(
                self._rate_correction + self._gain_int * timing_error,
                -self._max_rate_correction, self._max_rate_correction))
            # Proportional: reacts to this symbol's error, plus the rate correction.
            step_correction = float(np.clip(
                self._gain_prop * timing_error + self._rate_correction,
                -self._max_step_correction, self._max_step_correction))

            # 4. CONTROLLER: emit this symbol, then step to the next one.  Late (error < 0)
            # makes the step shorter; early (error > 0) makes it longer.
            symbols.append(symbol)
            positions.append(self._discarded + self._next_index + self._next_frac)
            self._prev_symbol = symbol
            self._next_index, self._next_frac = _normalize_position(
                self._next_index, self._next_frac + self._sps + step_correction)

        # KEEP ONLY WHAT THE NEXT SYMBOL STILL NEEDS
        # Its midpoint reaches back half a symbol, and interpolating there reads one sample
        # earlier still.  Everything before that can go.
        first_needed = _normalize_position(
            self._next_index, self._next_frac - self._half_symbol)[0] - _SAMPLES_BEFORE
        first_needed = min(max(first_needed, 0), signal.size)
        self._carryover = signal[first_needed:]
        self._next_index -= first_needed  # Integer shift: exact, so chunking can't change results
        self._discarded += first_needed

        # DONE
        self.last_offsets = np.asarray(positions)
        return np.asarray(symbols, dtype=np.complex64)

    def recover(self, burst: np.ndarray) -> np.ndarray:
        """Burst mode: reset the loop, then recover every symbol in one complete burst."""
        self.reset()
        return self.process(burst)

    def reset(self) -> None:
        """Return the loop to its initial state (e.g., at the start of a new burst)."""
        self._carryover = np.zeros(0, dtype=np.complex64)
        # First symbol starts one symbol in: far enough for its midpoint and the samples the
        # interpolator reads around it.  The loop pulls it onto the real peak from there.
        self._next_index = self._sps
        self._next_frac = 0.0
        self._rate_correction = 0.0
        self._prev_symbol = 0j
        self._discarded = 0


def _interpolate_cubic(signal: np.ndarray, index: int, frac: float) -> complex:
    """Estimate signal at position index + frac by fitting a cubic through 4 neighbors.

    Lagrange form: each neighbor is weighted by a cubic in frac that is 1 at its own position
    and 0 at the other three, so the curve passes through all four samples exactly.  frac = 0
    returns signal[index]; frac = 0.5 returns a smooth estimate halfway to signal[index + 1].

    Args:
        signal: The samples.
        index: Integer sample index (needs index >= 1 and index + 2 < len(signal)).
        frac: Fraction of a sample past index, in [0, 1).
    """
    before, at, after, after2 = (signal[index - 1], signal[index],
                                 signal[index + 1], signal[index + 2])
    return (before * (-frac * (frac - 1) * (frac - 2) / 6)
            + at * ((frac + 1) * (frac - 1) * (frac - 2) / 2)
            + after * (-(frac + 1) * frac * (frac - 2) / 2)
            + after2 * ((frac + 1) * frac * (frac - 1) / 6))


def _normalize_position(index: int, offset: float) -> tuple[int, float]:
    """Turn index + offset (any float) into (integer index, fraction in [0, 1)).

    Example: (10, 2.75) -> (12, 0.75) and (10, -0.25) -> (9, 0.75).  Keeping the integer part
    separate from the fraction keeps positions exact no matter how far the stream runs.
    """
    whole = int(np.floor(offset))
    return index + whole, offset - whole
