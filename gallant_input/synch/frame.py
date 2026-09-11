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
