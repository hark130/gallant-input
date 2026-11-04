"""Defines the SpectrumAnalysis dataclass."""

# Standard Imports
from dataclasses import dataclass
import numpy
# Third Party Imports
# Local Imports
from gallant_input.spectralpeak import SpectralPeak


@dataclass(frozen=True)
class SpectrumAnalysis:
    """Results of analyzing a sampled spectrum."""

    fft: numpy.ndarray
    frequencies: numpy.ndarray
    magnitudes: numpy.ndarray
    peaks: list[SpectralPeak]
