"""Implements the carrier recover CostasLoop class."""

# Standard Imports
# Third Party Imports
from numpy.typing import NDArray
import numpy as np
# Local Imports
from protoroad.validation import validate_ndarray


# pylint: disable=too-few-public-methods
class CostasLoop:
    """Second-order BPSK Costas loop for fine carrier recovery.

    Locks onto a signal's hidden carrier wave, using in-phase (I) and quadrature (Q) paths
    with a feedback loop.  It recovers phase and frequency without needing an extra pilot tone.
    """

    def __init__(self, loop_bandwidth: float = 0.05, damping_factor: float = 0.707) -> None:
        """CostasLoop ctor.

        Args:
            loop_bandwidth: [OPTIONAL] A normalized digital loop bandwidth expressed in
                radians/sample.  Start with a broad loop: 0.05–0.1.
                Then dial it in: 0.02, 0.01, 0.005.  The goal is to find the smallest bandwidth
                that still acquires reliably, tracks the expected frequency/phase drift,
                and maintains a low BER.
            damping_factor: [OPTIONAL] Controls how the internal oscillator responds to phase
                changes.  There are effectively three types of transient responses: over-damped,
                critically damped, and under-damped.  Over-damped (>1.0) - The loop responds very
                slowly, preventing overshoot but greatly increasing the time needed to achieve lock.
                Critically damped (0.707 to 1.0) - The loop reaches a locked state as fast as
                possible without any major phase ringing or overshoot.
                Under-damped (<0.707(depending on design?)) - The loop locks quickly, but the
                phase error overshoots and rings back and forth before settling.
        """
        # PUBLIC ATTRIBUTES
        # Ctor input
        self._loop_bandwidth = loop_bandwidth  # Expressed in radians/sample
        self._damping_factor = damping_factor  # Controls the internal oscillator response
        # Calculated second-order digital PLL coefficients (see: self._compute())
        # Adjusts the phase estimate based on the current phase error
        self._alpha = 0.0                      # Proportional gain coefficient
        # Accumulates the phase error over time to adjust freq estimate
        self._beta = 0.0                       # Integral gain coefficient
        # Track offsets as samples are processed
        self._phase = 0.0                      # Tracking phase offset
        self._frequency = 0.0                  # Tracking frequency offset

        # PRIVATE ATTRIBUTES
        self._computed = False                # Validate and calculate coefficients once

    def process(self, samples: NDArray[np.complexfloating]) -> NDArray[np.complexfloating]:
        """Recover the carrier phase from BPSK samples.

        Args:
            samples: The signal to recover carrier phase from.

        Returns:
            The samples corrected for carrier phase.

        Raises:
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        # LOCAL VARIABLES
        output = None  # Corrected samples

        # INPUT VALIDATION
        samples = validate_ndarray(samples, "samples", dtype=np.complex64, check_finite=True)

        # PREPARE
        self._compute()  # Validate and parse the input once

        # PROCESS IT
        output = np.empty_like(samples)
        for index, sample in enumerate(samples):
            # Rotate the input by the current phase estimate
            corrected = sample * np.exp(-1j * self._phase)
            # Save corrected sample
            output[index] = corrected
            # BPSK phase detector
            error = corrected.real * corrected.imag
            # Second-order loop filter
            self._frequency += self._beta * error
            self._phase += self._frequency + self._alpha * error
            # Wrap phase to [-pi, pi)
            self._phase = ((self._phase + np.pi) % (2.0 * np.pi)) - np.pi

        # DONE
        return output

    def _compute(self) -> None:
        """Calculate the validated input once.

        Call this method before doing anything.
        """
        if self._computed is not True:
            # Calculate the second-order digital PLL coefficients
            # Characteristic closed-loop transfer function polynomial denominator in the Z-domain
            denom = \
                1.0 + 2.0 * self._damping_factor * self._loop_bandwidth + self._loop_bandwidth**2
            # Proportional gain coefficient; Adjusts phase estimate based on the current phase error
            self._alpha = 4.0 * self._damping_factor * self._loop_bandwidth / denom
            # Integral gain coefficient; Accumulates phase error over time to adjust freq estimate
            self._beta = 4.0 * self._loop_bandwidth**2 / denom
            self._computed = True
# pylint: enable=too-few-public-methods
