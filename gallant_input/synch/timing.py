"""Defines common timing synchronization functionality."""

# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.signal import interpolate_samples
from gallant_input.validation import (validate_pos_float, validate_pos_float_or_int,
                                      validate_pos_int, validate_ndarray)


def recover_clock_mm(samples: numpy.ndarray, samples_per_symbol: float | int,
                     interp: int | None = None, loop_react: float = 0.3) -> numpy.ndarray:
    """Extricate symbols after recovering the clock using the Mueller and Muller technique.

    Why interpolate during clock recovery?  Symbol synchronizers tend to interpolate the input
    samples by some number, e.g., 16, so that it’s able to shift by a fraction of a sample.
    The random delay caused by the wireless channel will unlikely be an exact multiple of a
    sample, so the peak of the symbol may not actually happen on a sample.

    Args:
        samples: A real or complex signal to synchronize against.
        samples_per_symbol: The number of samples required to represent one symbol.
        interp: [OPTIONAL] If not None, the input samples will be interpolated.  If used, this
            value must be a positive integer.
        loop_react: [OPTIONAL] Changes how fast the feedback loop reacts.  A higher value will
            make it react faster but with higher risk of stability issues.

    Returns:
        An array of symbol 'soft decisions' (AKA soft bits) at the same data type as samples.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    mu = 0                 # Timing offset (updated each loop)
    soft_bits = None       # The output symbol decisions
    out_rail = None        # Stores values, each iteration
    in_index = 0           # Input samples index
    out_index = 2          # Output index
    loc_samples = samples  # Local copy of samples (which may be interpolated)

    # VALIDATION
    validate_ndarray(samples, 'samples', can_be_empty=False)
    validate_pos_float_or_int(samples_per_symbol, 'samples_per_symbol')
    validate_pos_float(loop_react, 'loop_react')
    if interp is not None:
        validate_pos_int(interp, 'interp')
        # SETUP
        loc_samples = interpolate_samples(samples=loc_samples, interp=interp)

    # RECOVER IT
    soft_bits = numpy.zeros(len(samples) + 10, dtype=samples.dtype)
    out_rail = numpy.zeros(len(samples) + 10, dtype=numpy.complex64)
    while out_index < len(samples) and in_index+16 < len(samples):
        if interp is None:
            soft_bits[out_index] = loc_samples[in_index]  # Grab what we think is the "best" sample
        else:
            soft_bits[out_index] = loc_samples[(in_index * interp) + int(mu * interp)]
        out_rail[out_index] = int(numpy.real(soft_bits[out_index]) > 0) \
            + 1j*int(numpy.imag(soft_bits[out_index]) > 0)
        x = (out_rail[out_index] - out_rail[out_index-2]) * numpy.conj(soft_bits[out_index-1])
        y = (soft_bits[out_index] - soft_bits[out_index-2]) * numpy.conj(out_rail[out_index-1])
        mm_val = numpy.real(y - x)
        mu += samples_per_symbol + (loop_react * mm_val)
        in_index += int(numpy.floor(mu))  # Round down to nearest int for use as an index
        mu = mu - numpy.floor(mu)  # Remove the integer part of mu
        out_index += 1  # Increment output index
    soft_bits = soft_bits[2:out_index]  # Trim the output array: remove place holders, match len

    # DONE
    return soft_bits
