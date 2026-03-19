"""Defines the ConvolveMode enum to communicate a convolution choice.

See:
    - https://brianmcfee.net/dstbook-site/content/ch03-convolution/Modes.html#
    - https://numpy.org/doc/2.1/reference/generated/numpy.convolve.html
    - https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.signal.convolve.html
"""

# Standard Imports
from enum import auto, IntEnum
from typing import Final
# Third Party Imports
# Local Imports

# PRIVATE CONSTANTS
_FULL: Final[int] = 1   # mode='full'
_SAME: Final[int] = 2   # mode='same'
_VALID: Final[int] = 3  # mode='valid'


class ConvolveMode(IntEnum):
    """Mode of convolution."""
    FULL = auto()   # Convolution at each point of overlap, with an output shape of (N+M-1,)
    SAME = auto()   # The convolution product returns an output of length max(M, N)
    VALID = auto()  # The convolution product is only given for points where overlap is complete

    @property
    def translate(self) -> str:
        """Convert the IntEnum.value into its convolve mode: 'full', 'same', or 'valid'.

        Returns:
            A string for use with the numpy.convolve(mode).

        Raises:
            NotImplementedError: Any IntEnum values added to SigMFDataType that weren't also
                implemented here.
        """
        mode_str = None  # The IntEnum value converted to the convolve mode string
        if self.value == _FULL:
            mode_str = 'full'
        elif self.value == _SAME:
            mode_str = 'same'
        elif self.value == _VALID:
            mode_str = 'valid'
        else:
            raise NotImplementedError('This property method has not yet added support '
                                      f'for "{self.name.title()}"')
        return mode_str
