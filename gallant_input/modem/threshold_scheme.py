"""Defines the ThresholdScheme IntEnum."""


# Standard Imports
from enum import auto, IntEnum
# Third Party Imports
# Local Imports


class ThresholdScheme(IntEnum):
    """Communicate intended threshold calculation scheme as an argument."""
    MIDRANGE = auto()  # Midpoint betweeen max and min value
    MEAN = auto()      # The average of all values
    KMEANS = auto()    # k-means clustering
