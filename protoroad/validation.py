"""Input validation shared across protoroad."""

# Standard Imports
# Third Party Imports
import numpy as np
from numpy.typing import DTypeLike
# Local Imports

KINDS_COMPLEX: str = "c"            # numpy dtype.kind letters: complex...
KINDS_NUMERIC: str = "fc"           # ...float or complex (real samples are fine to promote)
KINDS_INTEGER: str = "iub"          # ...signed int, unsigned int, or bool (e.g., bit arrays)


# pylint: disable=too-many-arguments
def validate_ndarray(array: np.ndarray, name: str = "array", *, kinds: str = KINDS_NUMERIC,
                     ndim: int = 1, allow_empty: bool = True, check_finite: bool = False,
                     dtype: DTypeLike | None = None) -> np.ndarray:
    """Validate an ndarray argument, then return it (optionally converted to dtype).

    Example Usage:
        samples = validate_ndarray(samples, "samples", dtype=np.complex64)
        if samples.size == 0:
            return samples  # Empty in, empty out

    Args:
        array: The argument to check.  Must already be an np.ndarray: a list or a scalar is
            almost always a caller bug, so it's rejected rather than silently converted.
        name: [OPTIONAL] The argument's name, for error messages.
        kinds: [OPTIONAL] Allowed dtype.kind letters; see the KINDS_* constants.
        ndim: [OPTIONAL] Required number of dimensions.
        allow_empty: [OPTIONAL] If False, an empty array raises.
        check_finite: [OPTIONAL] If True, NaN or inf raises.  Costs one pass over the data;
            worth it in front of stateful loops, where one NaN poisons the state for good.
        dtype: [OPTIONAL] If given, the returned array is converted to this dtype.

    Returns:
        The validated array, converted to dtype if one was given.

    Raises:
        TypeError: Not an np.ndarray, or a dtype kind not in kinds.
        ValueError: Wrong number of dimensions, empty when not allowed, or non-finite values.
    """
    # INPUT VALIDATION
    if not isinstance(array, np.ndarray):
        raise TypeError(f"{name} must be a numpy ndarray, got {type(array).__name__}")
    if array.dtype.kind not in kinds:
        raise TypeError(f"{name} must have a dtype of kind '{kinds}', got {array.dtype}")
    if array.ndim != ndim:
        raise ValueError(f"{name} must be {ndim}-D, got shape {array.shape}")
    if not allow_empty and array.size == 0:
        raise ValueError(f"{name} must not be empty")
    if check_finite and not np.all(np.isfinite(array)):
        raise ValueError(f"{name} contains NaN or inf")

    # DONE
    return array if dtype is None else array.astype(dtype, copy=False)
# pylint: enable=too-many-arguments
