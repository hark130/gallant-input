"""Defines the Endian IntEnum to positively communicate endianness."""

# Standard Imports
from enum import IntEnum
# Third Party Imports
# Local Imports


class Endian(IntEnum):
    """Endianness."""
    UNSPECIFIED = 0  # Unknown endianness or not applicable
    BIG = 2          # Big-endian
    LITTLE = 1       # Little-endian
