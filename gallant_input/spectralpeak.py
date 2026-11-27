"""Defines the SpectralPeak dataclass."""

# Standard Imports
from dataclasses import dataclass
# Third Party Imports
# Local Imports


@dataclass(frozen=True)
class SpectralPeak:
    """Describes a single peak detected within a spectrum."""

    frequency: float
    magnitude: float
    prominence: float
    left_edge: float
    right_edge: float
    bucket: int        # AKA FFT bin
