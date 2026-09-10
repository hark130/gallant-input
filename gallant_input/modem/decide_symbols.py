"""Defines the DecideSymbols Enum."""

# Standard Imports
from enum import auto, Enum
# Third Party Imports
# Local Imports


class DecideSymbols(Enum):
    """Communicate symbol decision strategy as an argument."""
    AXIS = auto()         # Quantize values to the nearest axis level on the complex plane
    KMEANS = auto()       # Use k-means clustering
    KMEANS_GAIN = auto()  # Use k-means clustering and correct channel gain
    NEAR = auto()         # Calculate the nearest constellation point
