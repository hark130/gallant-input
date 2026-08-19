"""Functionality to assist with frame synchronization."""

# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_ndarray
from gallant_input.validation import validate_ndarray


def correlate_it(haystack: bytes | numpy.ndarray, needle: bytes | numpy.ndarray) -> int:
    """Correlate needle with haystack returning a haystack index of highest correlation.

    Bipolar encoding (e.g., -1 and +1) is more effective for correlation than binary encoding
    (0 and 1) because the mathematical properties of negative values penalize mismatches and
    reward matches equally.  Any bytes objects will be converted to bipolar numpy.ndarray prior
    to correlation.

    Args:
        haystack: The source to correlate against (and index into).
        needle: The thing to find (the best index of) in the haystack.

    Returns:
        An index into haystack indicating the highest correlation of needle.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    loc_haystack = haystack     # Local copy of the haystack
    haystack_name = 'haystack'  # Argument name for Exceptions
    loc_needle = needle         # Local copy of the needle
    needle_name = 'needle'      # Argument name for Exceptions
    converted = ' (converted)'  # Update to default argument names
    corr = None                 # Correlation array
    index = 0                   # Index of highest correlation into the haystack

    # SETUP
    if isinstance(haystack, bytes):
        loc_haystack = convert_bin_bytes_to_ndarray(haystack, bipolar=True)
        haystack_name = haystack_name + converted
    if isinstance(needle, bytes):
        loc_needle = convert_bin_bytes_to_ndarray(needle, bipolar=True)
        needle_name = needle_name + converted

    # VALIDATION
    _validate_corr_arrays(loc_haystack, haystack_name, loc_needle, needle_name)

    # CORRELATE IT
    corr = numpy.correlate(loc_haystack, loc_needle, mode='valid')
    index = int(corr.argmax())

    # DONE
    return index


def find_frame_start(symbol_metrics: numpy.ndarray, preamble: numpy.ndarray,
                     threshold: float = 0.8) -> int:
    """Find the start of a frame by correlating bipolar symbol metrics with a known preamble.

    Args:
        symbol_metrics: Symbol-spaced, continuous-valued demodulator metrics.
        preamble: Expected bipolar preamble, typically containing -1.0 and +1.0.
        threshold: Minimum normalized correlation coefficient required to accept
            a preamble match.

    Returns:
        Index into symbol_metrics where the preamble begins or None if the score didn't
        meet the threshold.

    Raises:
        ValueError: Bad input value (e.g., array dimension, len, relative size).
        TypeError: Bad input type.
    """
    # LOCAL VARIABLES
    symbol_metrics = numpy.asarray(symbol_metrics, dtype=numpy.float32)
    preamble = numpy.asarray(preamble, dtype=numpy.float32)
    needle_norm = None   # Needle matrix norm
    correlations = None  # Correlation array

    # INPUT VALIDATION
    validate_ndarray(symbol_metrics, 'symbol_metrics',
                     can_be_empty=False, num_dim=1, must_be_complex=False)
    validate_ndarray(preamble, 'preamble',
                     can_be_empty=False, num_dim=1, must_be_complex=False)
    if symbol_metrics.size < preamble.size:
        raise ValueError(f'Unable to locate a preamble if symbol_metrics is shorter')

    # FIND IT
    # Remove DC from the two signals so correlation measures similarity
    # of the pattern rather than similarity of their absolute levels.
    needle = preamble - numpy.mean(preamble)
    # Normalize the needle once
    needle_norm = numpy.linalg.norm(needle)
    if needle_norm == 0:
        raise ValueError("The preamble must contain variation")
    correlations = numpy.empty(symbol_metrics.size - preamble.size + 1, dtype=numpy.float32)
    for i in range(correlations.size):
        window = symbol_metrics[i:i + preamble.size]  # Sliding window
        window = window - numpy.mean(window)  # Remove the local DC component
        window_norm = numpy.linalg.norm(window)  # Window matrix norm
        if window_norm == 0:
            correlations[i] = 0.0
            continue
        correlations[i] = (numpy.dot(window, needle) / (window_norm * needle_norm))
    # Find the strongest match.
    start = int(numpy.argmax(correlations))
    score = float(correlations[start])

    # DONE
    if score < threshold:
        # print(f'Best correlation was {score:.3f} but was below threshold {threshold:.3f}')
        start = None
    return start


def _validate_corr_arrays(haystack: numpy.ndarray, haystack_name: str,
                          needle: numpy.ndarray, needle_name: str) -> None:
    """Validate the correlation arrays under their own strength and against each other."""
    # LOCAL VARIABLES
    haystack_ndim = 0  # The number of dimensions in the haystack
    needle_ndim = 0    # The number of dimensions in the needle
    haystack_len = 0   # The length of haystack
    needle_len = 0     # The length of needle

    # VALIDATION
    # Basic
    validate_ndarray(haystack, haystack_name, can_be_empty=False,
                     num_dim=None, must_be_complex=False)
    validate_ndarray(needle, needle_name, can_be_empty=False,
                     num_dim=None, must_be_complex=False)
    # Update vars
    haystack_ndim = haystack.ndim
    needle_ndim = needle.ndim
    haystack_len = len(haystack)
    needle_len = len(haystack)
    # Haystack v. Needle
    if haystack_ndim != needle_ndim:
        raise ValueError(f'The haystack "{haystack_name}" (ndim {haystack_ndim}) must be '
                         f'the same dimension as the needle "{needle_name}" (ndim {needle_ndim})')
    if needle_len > haystack_len:
        raise ValueError(f'The length of the needle "{needle_name}" (len {needle_len}) may not be '
                         f'longer than the haystack "{haystack_name}" (len {haystack_len})')
