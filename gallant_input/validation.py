"""Common-use validation functionality.

This module defines how variables are type-validated, and how string and list parameters are
validated.

    Typical usage example:

    from gallant_input.validation import validate_list, validate_string, validate_type

    validate_list(self._options, 'options', can_be_empty=True)
    validate_string(self._makefile_rule, 'makefile_rule')
    validate_type(self._as_root, 'as_root', bool)
"""
# Standard Imports
from pathlib import Path
from typing import Any, Final
# Third Party Imports
# Local Imports

# Template string for arguments of the wrong data type
_BAD_TYPE: Final[str] = 'The "{}" argument should have been of type "{}" but was "{}" instead'
# Template string for arguments that may not be empty
_BAD_VAL_EMPTY: Final[str] = 'The "{}" argument can not be empty'


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
        validate_type(exact_len, 'exact_len', int)
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
    """
    # LOCAL VARIABLES
    exp_type = f'{bytes} or {str}'  # The expected data types

    # VALIDATE IT
    if not _validate_type(validate_this, bytes) and not _validate_type(validate_this, str):
        raise TypeError(_BAD_TYPE.format(param_name, exp_type, type(validate_this)))


def validate_file(validate_this: Path, param_name: str, must_exist: bool = True) -> None:
    """Validate validate_this as a Path ojbect to a file that exists.

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


def validate_path(validate_this: Path, param_name: str, must_exist: bool = True) -> None:
    """Validate validate_this as a Path ojbect to a path that exists.

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
    validate_type(must_exist, 'must_exist', bool)
    validate_type(validate_this, param_name, Path)
    if must_exist and not validate_this.exists():
        raise FileNotFoundError(f'Unable to locate "{param_name}" path: '
                                f'"{str(validate_this.absolute())}"')


def validate_int(validate_this: Path, param_name: str) -> None:
    """Validate validate_this as an int ojbect.

    Args:
        validate_this: The parameter to validate.
        param_name: The name of the parameter to be used in exception messages.

    Raises:
        TypeError: validate_this is not an int.
    """
    # VALIDATION
    validate_type(validate_this, param_name, int)


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
    validate_int(validate_this, param_name, int)
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
