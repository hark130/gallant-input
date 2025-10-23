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


# Template string for arguments that may not be empty
_BAD_VAL_EMPTY: Final[str] = 'The "{}" argument can not be empty'


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
    if not isinstance(var, var_type):
        raise TypeError(f'The "{var_name}" argument should have been of type "{var_type}" '
                        f'but was "{type(var)}" instead')
