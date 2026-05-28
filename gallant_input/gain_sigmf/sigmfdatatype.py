"""Defines the SigMFDataType enum for SigMF Dataset Format data types.

See: https://sigmf.org/#sigmf-dataset-format
"""

# Standard Imports
from enum import IntEnum
from typing import Final
# Third Party Imports
# Local Imports

# PRIVATE CONSTANTS
_UNDEFINED: Final[int] = 0  # No SigMF dataset format type or undefined
_FLOAT: Final[int] = 1      # Floating-point:   'f'
_INT: Final[int] = 2        # Signed-integer:   'i'
_UINT: Final[int] = 3       # Unsigned-integer: 'u'


class SigMFDataType(IntEnum):
    """SigMF Dataset Format data types."""
    UNDEFINED = _UNDEFINED  # No SigMF dataset format type or undefined
    FLOAT = _FLOAT          # Floating-point:   'f'
    INT = _INT              # Signed-integer:   'i'
    UINT = _UINT            # Unsigned-integer: 'u'

    @property
    def translate(self) -> str:
        """Convert the IntEnum.value into its SigMF code: 'f', 'i', or 'u'.

        Returns:
            A single character representation of the Dataset Format.

        Raises:
            LookupError: SigMFDataType.UNDEFINED
            NotImplementedError: Any IntEnum values added to SigMFDataType that weren't also
                implemented here.
        """
        sigmf_code = None  # The IntEnum value converted to SigMF Dataset Format data type code
        if self.value == _FLOAT:
            sigmf_code = 'f'
        elif self.value == _INT:
            sigmf_code = 'i'
        elif self.value == _UINT:
            sigmf_code = 'u'
        elif self.value == _UNDEFINED:
            raise LookupError(f'No SigMF code exists for "{self.name.title()}"')
        else:
            raise NotImplementedError('This property method has not yet added support '
                                      f'for "{self.name.title()}"')
        return sigmf_code
