"""Defines the PulseShape Enum."""


# Standard Imports
from enum import auto, Enum
# Third Party Imports
# Local Imports


class PulseShape(Enum):
    """Communicate intended pulse shaping as an argument."""
    NONE = auto()        # Do not apply any pulse shaping
    RAIS_COS = auto()    # Raised-Cosine Filter
    RRC = auto()         # Root Raised-Cosine (RRC) Filter
    GAUSS = auto()       # Gaussian Filter
    SINC = auto()        # Sinc Filter
    RECT_PULSE = auto()  # Rectangular (Square) Pulse
