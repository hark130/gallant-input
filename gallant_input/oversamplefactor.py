"""Defines the OversampleFactor IntEnum to rationally limit oversampling in the frequency domain."""

# Standard Imports
from enum import IntEnum
# Third Party Imports
# Local Imports


class OversampleFactor(IntEnum):
    """An oversampling factor, commonly specified as K, in the frequency domain.

    This value controls how densely the filter’s frequency response is sampled:
        Larger values --> smoother plot
        Smaller values --> coarser plot
    """
    MINIMAL = 4    # Minimal smoothing for quick/debug computation
    DECENT = 8     # Decent smoothing for general use
    DEFAULT = 16   # Default value for most uses
    SMOOTH = 32    # Smooth results for analysis
    OVERKILL = 64  # Rarely needed
    INSANE = 128   # Go bananas
