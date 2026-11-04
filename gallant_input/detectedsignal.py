"""Defines the DetectedSignal dataclass."""

# Standard Imports
from dataclasses import dataclass
# Third Party Imports
# Local Imports
from gallant_input.spectralpeak import SpectralPeak


@dataclass(frozen=True)
class DetectedSignal:
    """Describes one detected RF signal."""

    center_frequency: float
    bandwidth: float
    peaks: list[SpectralPeak]
