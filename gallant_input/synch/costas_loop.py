"""Implements the carrier recover CostasLoop class."""

# Standard Imports
# Third Party Imports
from numpy.typing import NDArray
import numpy
# Local Imports
from gallant_input.validation import (validate_bool, validate_float, validate_ndarray,
                                      validate_pos_float)


class CostasLoop:
    """Second-order BPSK Costas loop for fine carrier recovery.

    Locks onto a signal's hidden carrier wave, using in-phase (I) and quadrature (Q) paths
    with a feedback loop.  It recovers phase and frequency without needing an extra pilot tone.
    """

    def __init__(self, loop_bandwidth: float = 0.01, damping_factor: float = 0.707) -> None:
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
        self.loop_bandwidth = loop_bandwidth  # Expressed in radians/sample
        self.damping_factor = damping_factor  # Controls the internal oscillator response
        # Calculated second-order digital PLL coefficients (see: self._compute())
        # Adjusts the phase estimate based on the current phase error
        self.alpha = 0.0                      # Proportional gain coefficient
        # Accumulates the phase error over time to adjust freq estimate
        self.beta = 0.0                       # Integral gain coefficient
        # Track offsets as samples are processed
        self.phase = 0.0                      # Tracking phase offset
        self.frequency = 0.0                  # Tracking frequency offset

        # PRIVATE ATTRIBUTES
        self._computed = False                # Validate and calculate coefficients once

    def process(self, samples: NDArray[numpy.complexfloating]) -> NDArray[numpy.complexfloating]:
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
        validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                         must_be_complex=True)

        # PREPARE
        self._compute()  # Validate and parse the input once

        # PROCESS IT
        output = numpy.empty_like(samples)
        for index, sample in enumerate(samples):
            # Rotate the input by the current phase estimate
            corrected = sample * numpy.exp(-1j * self.phase)
            # Save corrected sample
            output[index] = corrected
            # BPSK phase detector
            error = corrected.real * corrected.imag
            # Second-order loop filter
            self.frequency += self.beta * error
            self.phase += self.frequency + self.alpha * error
            # Wrap phase to [-pi, pi)
            self.phase = ((self.phase + numpy.pi) % (2.0 * numpy.pi)) - numpy.pi

        # DONE
        return output

    def validate(self) -> None:
        """Validate the attributes."""
        # Ctor Args
        validate_pos_float(self.loop_bandwidth, 'loop_bandwidth')
        validate_pos_float(self.damping_factor, 'damping_factor')
        # Attributes
        validate_float(self.phase, 'phase attribute')
        validate_float(self.frequency, 'frequency attribute')
        validate_float(self.alpha, 'alpha attribute')
        validate_float(self.beta, 'beta attribute')
        validate_bool(self._computed, 'private _computed attribute')

    def _compute(self) -> None:
        """Calculate the validated input once.

        Call this method before doing anything.
        """
        self.validate()
        if self._computed is not True:
            # Calculate the second-order digital PLL coefficients
            # Characteristic closed-loop transfer function polynomial denominator in the Z-domain
            denom = 1.0 + 2.0 * self.damping_factor * self.loop_bandwidth + self.loop_bandwidth**2
            # Proportional gain coefficient; Adjusts phase estimate based on the current phase error
            self.alpha = 4.0 * self.damping_factor * self.loop_bandwidth / denom
            # Integral gain coefficient; Accumulates phase error over time to adjust freq estimate
            self.beta = 4.0 * self.loop_bandwidth**2 / denom
            self._computed = True
