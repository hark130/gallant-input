"""Common-use validation functionality.

This module defines how variables are type-validated, and how string and list parameters are
validated.

    Typical usage example:

    from gallant_input.validation import validate_bool, validate_list, validate_string

    validate_bool(self._as_root, 'as_root')
    validate_list(self._options, 'options', can_be_empty=True)
    validate_string(self._makefile_rule, 'makefile_rule')
"""
# Standard Imports
from collections.abc import Callable
from pathlib import Path
from typing import Any, Final
import math
# Third Party Imports
from numpy import asarray
from numpy.typing import ArrayLike
import numpy
# Local Imports

# Template string for arguments of the wrong data type
_BAD_TYPE: Final[str] = 'The "{}" argument should have been of type "{}" but was "{}" instead'
# Template string for arguments that may not be empty
_BAD_VAL_EMPTY: Final[str] = 'The "{}" argument can not be empty'


def validate_arraylike(array_like: ArrayLike, param_name: str, num_dim: int | None = None) -> None:
    """Validate a NumPy 1-dimensional array_like data type.

    Args:
        array_like: Includes, but is not(?) limited to, the following data types: list, tuple,
            range, numpy.array.
        param_name: The name of the parameter to be used in exception messages.
        num_dim: [OPTIONAL] If num_dim is an integer, the number of dimensions of the array_like
            object will be tested against this value.  Otherwise, the number of dimensions will
            be ignored.

    Raises:
        TypeError: Invalid data type (essentially, it was rejected by numpy.asarray()).
        ValueError: Bad value (it wasn't 1-dimensional).
    """
    # LOCAL VARIABLES
    arr = None  # Test array

    # INPUT VALIDATION
    validate_string(validate_this=param_name, param_name='param_name', can_be_empty=False)
    if num_dim is not None:
        validate_int(num_dim, 'num_dim')
        if num_dim < 0:
            raise ValueError(f'The "num_dim" argument may not be negative: {num_dim}')

    # VALIDATE IT
    try:
        arr = asarray(array_like)
    except TypeError as err:
        raise TypeError(f'The data type of the "{param_name}" value was rejected: {err}') from err
    except ValueError as err:
        raise ValueError(f'The "{param_name}" value was rejected: {err}') from err
    _validate_arraylike_ndim(arr, param_name, num_dim)


def validate_binary_bytes(validate_this: bytes, param_name: str, exact_len: int = None) -> None:
    """Validate a bytes object representation of binary data to a certain length.

    Args:
        validate_this: A bytes object containing binary to validate.
        param_name: The name of the parameter to be used in exception messages.
        exact_len: [OPTIONAL] If greater than -1, the exact length of validate_this is verified
            against this value (e.g., exact_len=0 verifies validate_this is empty).

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value (e.g., "...and I thought I saw a 2" -Bender).
    """
    validate_bytes(validate_this, param_name, exact_len)
    # Content
    if not all(bin_char in b'01' for bin_char in validate_this):
        raise ValueError(f'Invalid binary value detected in "{param_name}"')


def validate_bool(validate_this: bytes, param_name: str) -> None:
    """Validate a variable as a bool.

    Args:
        validate_this: An object to validate as a bool.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: Invalid data type.
    """
    validate_type(var=validate_this, var_name=param_name, var_type=bool)


def validate_bytes(validate_this: bytes, param_name: str, exact_len: int = None) -> None:
    """Validate a bytes object to a certain length.

    Args:
        validate_this: A bytes object to validate.
        param_name: The name of the parameter to be used in exception messages.
        exact_len: [OPTIONAL] If greater than -1, the exact length of validate_this is verified
            against this value (e.g., exact_len=0 verifies validate_this is empty).

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value (e.g., exact_len is a positive integer but validate_this doesn't
            measure up).
    """
    # LOCAL VARIABLES
    validate_len = False  # Validate the length of validate_this against exact_len
    act_len = 0           # Actual length of validate_this

    # INPUT VALIDATION
    # param_name
    validate_string(validate_this=param_name, param_name='param_name', can_be_empty=False)
    # exact_len
    if exact_len is not None:
        validate_int(exact_len, 'exact_len')
        if exact_len > -1:
            validate_len = True
    # validate_this
    validate_type(validate_this, param_name, bytes)
    if validate_len:
        act_len = len(validate_this)
        if act_len != exact_len:
            raise ValueError(f'The "{param_name}" argument must be of length "{exact_len}" '
                             f'instead of "{act_len}"')


def validate_bytes_or_str(validate_this: bytes | str, param_name: str) -> None:
    """Validate one of two data types: bytes, str.

    Args:
        validate_this: A bytes object to validate as a bytes object or a string.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not a bytes object or a string.
    """
    # LOCAL VARIABLES
    exp_type = f'{bytes} or {str}'  # The expected data types

    # VALIDATE IT
    if not _validate_type(validate_this, bytes) and not _validate_type(validate_this, str):
        raise TypeError(_BAD_TYPE.format(param_name, exp_type, type(validate_this)))


def validate_callable(validate_this: Callable, param_name: str) -> None:
    """Validate validate_this as a callable.

    Args:
        validate_this: A callable.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not a callable.
    """
    if not callable(validate_this):
        raise TypeError(_BAD_TYPE.format(param_name, Callable, type(validate_this)))


def validate_file(validate_this: Path, param_name: str, must_exist: bool = True) -> None:
    """Validate validate_this as a Path object to a file that exists.

    Args:
        validate_this: A Path object to a file that exists.
        param_name: The name of the parameter to be used in exception messages.
        must_exist: Optional; If False, ignores missing files.

    Raises:
        FileNotFoundError: must_exist is True but validate_this is not found.
        OSError: validate_this exists but is not a file (regardless of must_exist).
        TypeError: validate_this is not a Path object.
    """
    # INPUT VALIDATION
    validate_path(validate_this, param_name, must_exist)
    if validate_this.exists() and not validate_this.is_file():
        raise OSError(f'The "{param_name}" argument '
                      f'"{str(validate_this.absolute())}" is not a file')


def validate_float(validate_this: float, param_name: str) -> None:
    """Validate validate_this as a float object.

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not a float.
    """
    # VALIDATION
    validate_type(validate_this, param_name, float)


def validate_int(validate_this: int, param_name: str) -> None:
    """Validate validate_this as an int object.

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not an int.
    """
    # VALIDATION
    validate_type(validate_this, param_name, int)


def validate_float_or_complex(validate_this: float | complex, param_name: str) -> None:
    """Validate an argument, which could be an float or complex, on behalf of this package.

    The codec module will accept these data types within the mapper argument so this function will
    be used as a SPOT for all(?) float or complex validation.

    Args:
        validate_this: The parameter to validate as an int or float.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not a float or complex.
    """
    # LOCAL VARIABLES
    valid = False  # Flow control variable

    # VALIDATE IT
    # int?
    try:
        validate_float(validate_this, param_name)
    except TypeError:
        pass  # Ignoring one failure
    else:
        valid = True
    # float?
    if not valid:
        try:
            validate_type(validate_this, param_name, complex)
        except TypeError:
            # I don't want to "raise from" because this exception is shared by two try/excepts
            # pylint: disable=raise-missing-from
            raise TypeError(f'The "{param_name}" argument must be a float or complex '
                            f'data type instead of type {type(validate_this)}')
            # pylint: enable=raise-missing-from


def validate_int_or_float(validate_this: int | float, param_name: str) -> None:
    """Validate an argument, which could be an int or float, on behalf of this package.

    Many arguments are being implemented as int | float in this package
    (e.g., sample rate, sample spacing) so this function will be used as a SPOT for validation.

    Args:
        validate_this: The parameter to validate as an int or float.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not a int or float.
    """
    # LOCAL VARIABLES
    valid = False  # Flow control variable

    # VALIDATE IT
    # int?
    try:
        validate_int(validate_this, param_name)
    except TypeError:
        pass  # Ignoring one failure
    else:
        valid = True
    # float?
    if not valid:
        try:
            validate_float(validate_this, param_name)
        except TypeError:
            # I don't want to "raise from" because this exception is shared by two try/excepts
            # pylint: disable=raise-missing-from
            raise TypeError(f'The "{param_name}" argument must be an integer or floating point '
                            f'data type instead of type {type(validate_this)}')
            # pylint: enable=raise-missing-from


def validate_list(validate_this: list, param_name: str, can_be_empty: bool = True) -> None:
    """Standardizes how this module validates list parameters.

    Verifies validate_this is a list. Type validation is handled by validate_type().

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.
        can_be_empty: Optional; If False, this function verifies validate_this is not empty.

    Raises:
        TypeError: validate_this is not a list.
        ValueError: validate_this is empty and can_be_empty is False.
    """
    # VALIDATION
    validate_type(validate_this, param_name, list)
    if not validate_this and not can_be_empty:
        raise ValueError(_BAD_VAL_EMPTY.format(param_name))


def validate_ndarray(array: numpy.ndarray, array_name: str, can_be_empty: bool = False,
                     num_dim: int | None = None, must_be_complex: bool = False) -> None:
    """Validate numpy.ndarray objects on behalf of the module.

    Args:
        array: The object to validate as a numpy.ndarray.
        array_name: The name of the original argument to use in Exception messages.
        can_be_empty: [OPTIONAL] If True, array may be empty.  Otherwise, it must contain at least
            one element (or a ValueError exception is raised).
        num_dim: [OPTIONAL] If num_dim is an integer, the number of dimensions of array
            will be tested against this value.  Otherwise, the number of dimensions will
            be ignored.
        must_be_complex: [OPTIONAL] If True, array will be verified to hold complex samples.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # ARGUMENT VALIDATION
    validate_bool(validate_this=can_be_empty, param_name='can_be_empty')
    validate_bool(validate_this=must_be_complex, param_name='must_be_complex')
    validate_type(var=array, var_name=array_name, var_type=numpy.ndarray)
    if not can_be_empty and len(array) <= 0:
        raise ValueError(f'The "{array_name}" ndarray may not be empty')
    if num_dim is not None:
        validate_int(num_dim, 'num_dim')
        if num_dim < 0:
            raise ValueError(f'The "num_dim" argument may not be negative: {num_dim}')
        _validate_arraylike_ndim(array, array_name, num_dim)
    if must_be_complex:
        if not numpy.iscomplexobj(array):
            raise ValueError(f'The "{array_name}" ndarray must contain complex values')


def validate_path(validate_this: Path, param_name: str, must_exist: bool = True) -> None:
    """Validate validate_this as a Path object to a path that exists.

    Args:
        validate_this: A Path object to a path that exists.
        param_name: The name of the parameter to be used in exception messages.
        must_exist: Optional; If False, ignores missing files.

    Raises:
        FileNotFoundError: must_exist is True but validate_this is not found.
        TypeError: validate_this is not a Path object.
    """
    # INPUT VALIDATION
    validate_string(param_name, 'param_name', can_be_empty=True)
    validate_bool(must_exist, 'must_exist')
    validate_type(validate_this, param_name, Path)
    if must_exist and not validate_this.exists():
        raise FileNotFoundError(f'Unable to locate "{param_name}" path: '
                                f'"{str(validate_this.absolute())}"')


def validate_phase(phase: float, param_name: str) -> None:
    """Validate phase within the bounds of 0 and 2π, inclusive."""
    upper_bound = 2 * math.pi  # Upper limit for phase
    validate_float(phase, param_name)
    if phase < 0:
        raise ValueError(f'The {param_name} value may not be negative: {phase}')
    if phase > upper_bound:
        raise ValueError(f'The {param_name} value may not be greater than {upper_bound}: '
                         f'{phase}')


def validate_pos_float(validate_this: float, param_name: str, abs_tol: float = 1e-9) -> None:
    """Validate validate_this as a positive float.

    IMPORTANT NOTE: Positive values are greater than zero.  To put it another way, zero is
    *NOT* positive.

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.
        abs_tol: [OPTIONAL] The maximum difference for being considered "close" to zero,
            regardless of the magnitude of the input values.  This value is used to test if
            validate_this is equivalent to zero.  (see: math.isclose(abs_tol) for more information)

    Raises:
        TypeError: Not a float.
        ValueError: validate_this is not positive or abs_tol is negative.
    """
    # VALIDATION
    validate_float(validate_this, param_name)  # validate_this
    validate_float(abs_tol, 'abs_tol')  # abs_tol
    if abs_tol < 0:
        raise ValueError(f'The "abs_tol" value "{abs_tol}" may not be negative')
    if validate_this <= 0 and math.isclose(validate_this, 0, abs_tol=abs_tol):
        raise ValueError(f'The "{param_name}" argument may not be 0')
    if validate_this < 0:
        raise ValueError(f'The "{param_name}" argument *must* be > 0')


def validate_pos_float_or_int(validate_this: float | int, param_name: str,
                              abs_tol: float = 1e-9) -> None:
    """Validate validate_this as a positive float or int.

    IMPORTANT NOTE: Positive values are greater than zero.  To put it another way, zero is
    *NOT* positive.

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.
        abs_tol: [OPTIONAL] The maximum difference for being considered "close" to zero,
            regardless of the magnitude of the input values.  This value is used to test if
            validate_this is equivalent to zero.  (see: math.isclose(abs_tol) for more information)

    Raises:
        TypeError: Not a float or int.
        ValueError: validate_this is not positive or abs_tol is negative.
    """
    # LOCAL VARIABLES
    valid = False  # Flow control variable

    # INPUT VALIDATION
    validate_string(param_name, 'param_name', can_be_empty=True)
    validate_pos_float(abs_tol, 'abs_tol')
    validate_int_or_float(validate_this, param_name)

    # VALIDATE IT
    # positive int?
    try:
        validate_pos_int(validate_this, param_name)
    except TypeError:
        pass  # Ignoring one failure
    else:
        valid = True
    # positive float?
    if not valid:
        try:
            validate_pos_float(validate_this, param_name, abs_tol)
        except TypeError:
            # I don't want to "raise from" because this exception is shared by two try/excepts
            # pylint: disable=raise-missing-from
            raise TypeError(f'The "{param_name}" argument must be an integer or a '
                            f'floating point data type instead of type {type(validate_this)}')
            # pylint: enable=raise-missing-from


def validate_pos_int(validate_this: int, param_name: str) -> None:
    """Validate validate_this as a positive integer.

    IMPORTANT NOTE: Positive integers are greater than zero.  To put it another way, zero is
    *NOT* positive.

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not a positive integer.
        ValueError: validate_this is not positive.
    """
    # VALIDATION
    validate_int(validate_this, param_name)
    if validate_this <= 0:
        raise ValueError(f'The "{param_name}" argument is not positive')


def validate_string(validate_this: str, param_name: str, can_be_empty: bool = False) -> None:
    """Standardizes how this module validates string parameters.

    Verifies validate_this is a string. Type validation is handled by validate_type().

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.
        can_be_empty: Optional; If False, this function verifies validate_this is not empty.

    Raises:
        TypeError: validate_this is not a string.
        ValueError: validate_this is empty and can_be_empty is False.
    """
    # VALIDATION
    validate_type(validate_this, param_name, str)
    if not validate_this and not can_be_empty:
        raise ValueError(_BAD_VAL_EMPTY.format(param_name))


def validate_type(var: Any, var_name: str, var_type: type) -> None:
    """Standardizes how variables are type-validated.

    Verifies var is the same type represented in var_type. This function does not validate input.

    Args:
        var: The variable to type-validate.
        var_name: The name of the variable to be used in exception messages.
        var_type: The expected variable type.

    Raises:
        TypeError: Invalid data type.
    """
    if not _validate_type(var, var_type):
        raise TypeError(_BAD_TYPE.format(var_name, var_type, type(var)))


def _validate_arraylike_ndim(var: ArrayLike, var_name: str, num_dim: int | None) -> None:
    """Standardizes how the dimensions of ArrayLike variables are evaluated.

    This function will *not* validate the data type of var, var_name, or num_dim (other than
    testing it for None).  Instead, it assumes the data types are valid and immediately checks
    the number of dimensions.

    Args:
        var: Includes, but is not(?) limited to, the following data types: list, tuple,
            range, numpy.array.
        var_name: The name of the parameter to be used in exception messages.
        num_dim: [OPTIONAL] If num_dim is an integer, the number of dimensions of the array_like
            object will be tested against this value.  Otherwise, the number of dimensions will
            be ignored.

    Raises:
        ValueError: The var argument's number of dimensions does not match num_dim.
    """
    if num_dim is not None:
        if var.ndim != num_dim:
            raise ValueError(f'The "{var_name}" value is {var.ndim}-dimensional instead '
                             f'of {num_dim}-dimensional')


def _validate_type(var: Any, var_type: type) -> bool:
    """Standardizes how variables are evaluated against a data type.

    Args:
        var: The variable to type-validate.
        var_type: The expected variable type.

    Returns:
        True if var is of type var_type, False otherwise.
    """
    # LOCAL VARIABLES
    is_valid = False  # Is var of type var_type?

    # VALIDATE IT
    if isinstance(var, var_type):
        is_valid = True

    # DONE
    return is_valid
