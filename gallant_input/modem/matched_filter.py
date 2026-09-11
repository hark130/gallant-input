"""Defines the MatchedFilter IntEnum."""


# Standard Imports
from enum import auto, IntEnum
# Third Party Imports
# Local Imports


class MatchedFilter(IntEnum):
    """Communicate intended matched filter as an argument."""
    NONE = auto()      # Do not apply a matched filter
    RECT_FIR = auto()  # Rectangular Finite Impulse Response (FIR)
    RRC = auto()       # Root Raised-Cosine (RRC) Filter
    RAIS_COS = auto()  # Raised-Cosine Filter
    GAUSS = auto()     # Gaussian Filter
