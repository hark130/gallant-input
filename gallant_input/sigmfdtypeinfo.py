"""Defines the SigMFDTypeInfo() dataclass to answer questions about SigMF Dataset Format values.

USAGE:
    from gallant_input.sigmfdtypeinfo import SigMFDTypeInfo
    from gallant_input.endian import Endian

    sdf_val1 = SigMFDTypeInfo('cf32_le')
    sdf_val1.is_complex  # True
    sdf_val1.get_dtype   # dtype('float32')
    sdf_val1.is_signed   # True
    sdf_val1.get_endian  # Endian.LITTLE

    sdf_val2 = SigMFDTypeInfo('ru8')
    sdf_val2.is_complex  # False
    sdf_val2.get_dtype   # dtype('uint8')
    sdf_val2.is_signed   # False
    sdf_val2.get_endian  # Endian.UNSPECIFIED
"""

# Standard Imports
from dataclasses import dataclass, field
from typing import Any, Final
# Third Party Imports
from sigmf import sigmffile
from sigmf.error import SigMFError
import numpy
# Local Imports
from gallant_input.endian import Endian
from gallant_input.validation import validate_bool, validate_string, validate_type


# SigMF dtype_info dictionary keys
_SIG_DINFO_KEY_COMP_DTYPE: Final[str] = 'component_dtype'
_SIG_DINFO_KEY_COMPLEX: Final[str] = 'is_complex'
_SIG_DINFO_KEY_UNSIGNED: Final[str] = 'is_unsigned'
_SIG_DINFO_KEY_MAP_TYPE: Final[str] = 'memmap_map_type'


@dataclass()
class SigMFDTypeInfo():
    """Parse and answer questions about SigMF Dataset Format values.

    Utilizes sigmf.sigmffile.dtype_info() and then translates the dictionary values.

    Arguments:
        dataset: The SigMF Dataset Format value, as a string, to parse.
    """

    # Public Attributes
    dataset: str  # SigMF Dataset Format value

    # Private Attributes
    _dtype_dict: dict = None
    _validated: bool = field(default=False, repr=False)

    # CORE METHODS
    # In alphabetical order

    def validate_content(self) -> None:
        """Validate the contents of the dataclass: type, content, length, format, etc.

        Raises:
            RuntimeError: A SigMF-specific exception was raised (see: help(sigmf.error) for details)
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        if self._validated is not True:
            validate_bool(self._validated, 'internal attribute _validated')
            validate_string(validate_this=self.dataset, param_name='dataset', can_be_empty=False)
            self._validate_dataset_format()
            self._validated = True

    # HUMAN-READABLE METHODS
    # In alphabetical order

    @property
    def get_dtype(self) -> numpy.dtype:
        """Determines the dataset's component data type.

        Returns:
            A numpy.dtype object.

        Raises:
            KeyError: The necessary key was missing.
            RuntimeError: A SigMF-specific exception was raised (see: help(sigmf.error) for details)
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        self.validate_content()
        return numpy.dtype(_get_safe_key(self._dtype_dict, _SIG_DINFO_KEY_COMP_DTYPE, silent=False))

    @property
    def get_endian(self) -> Endian:
        """Determine the endianness of the dataset.

        Returns:
            An Endian object indicating the endianness.

        Raises:
            KeyError: The necessary key was missing.
            RuntimeError: A SigMF-specific exception was raised (see: help(sigmf.error) for details)
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        self.validate_content()
        map_type = _get_safe_key(self._dtype_dict, _SIG_DINFO_KEY_MAP_TYPE, silent=True)
        return _determine_endianness(map_type)

    @property
    def is_complex(self) -> bool:
        """Determines if dataset is complex or real.

        Returns:
            True if complex.  False if it's real.

        Raises:
            KeyError: The necessary key was missing.
            RuntimeError: A SigMF-specific exception was raised (see: help(sigmf.error) for details)
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        self.validate_content()
        return _get_safe_key(self._dtype_dict, _SIG_DINFO_KEY_COMPLEX, silent=False)

    @property
    def is_signed(self) -> bool:
        """Determines if dataset is signed or unsigned.

        Returns:
            True if signed.  False if it's unsigned.

        Raises:
            KeyError: The necessary key was missing.
            RuntimeError: A SigMF-specific exception was raised (see: help(sigmf.error) for details)
            TypeError: Bad data type.
            ValueError: Bad value.
        """
        self.validate_content()
        return not _get_safe_key(self._dtype_dict, _SIG_DINFO_KEY_UNSIGNED, silent=False)

    # PRIVATE METHODS
    # In alphabetical order

    def _validate_dataset_format(self) -> None:
        """Validate the content of self.dataset utilizing sigmf and store the dictionary."""
        try:
            self._dtype_dict = sigmffile.dtype_info(self.dataset)
        except SigMFError as err:
            raise RuntimeError(f'The "dataset" value "{self.dataset}" failed SigMF validation '
                               f'with a bespoke Exception: {err}') from err
        except TypeError as err:
            raise TypeError(f'The "dataset" value "{self.dataset}" failed SigMF'
                            f'type validation: {err}') from err
        except ValueError as err:
            raise ValueError(f'The "dataset" value "{self.dataset}" failed '
                             f'basic SigMF validation: {err}') from err
        validate_type(self._dtype_dict, 'internal attribute _dtype_dict', dict)


def _determine_endianness(map_type) -> Endian:
    """Determine a SigMF data type's endianness.

    This function is intended to infer the endianness from the
    _SIG_DINFO_KEY_MAP_TYPE key's value in the dictionary returned by sigmf.sigmffile.dtype_info().

    Returns:
        An Endian value indicating what was found.  Endian.UNSPECIFIED is used for all errors,
        exceptions, and (most?) 8-bit values.

    Raises:
        None.  All raises are translated into Endian.UNSPECIFIED instead.
    """
    # LOCAL VARIABLES
    endianness = Endian.UNSPECIFIED  # The result

    # DETERMINE IT
    try:
        validate_string(map_type, 'map_type', can_be_empty=False)
    except (TypeError, ValueError):
        pass
    else:
        if map_type.startswith('<'):
            endianness = Endian.LITTLE
        elif map_type.startswith('>'):
            endianness = Endian.BIG

    # DONE
    return endianness


# Leave me be, Pylint
# pylint: disable=broad-exception-caught
def _get_safe_key(dictionary: dict, key: Any, silent: bool = True) -> Any:
    """Safely get a key's value from a dictionary.

    Returns:
        Key value on success, None on any Exception.
    """
    # LOCAL VARIABLES
    value = None  # The key's value

    # INPUT VALIDATION
    validate_bool(silent, 'silent')

    # GET IT
    try:
        value = dictionary[key]
    except Exception as err:
        if not silent:
            raise err from err

    # DONE
    return value
# pylint: enable=broad-exception-caught
