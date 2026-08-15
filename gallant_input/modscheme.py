"""Defines the ModScheme IntEnum."""

# Standard Imports
from enum import auto, IntEnum
# Third Party Imports
# Local Imports


class ModScheme(IntEnum):
    """Communicates anticipated modulation scheme."""
    NONE = auto()  # Unknown
    OOK = auto()   # On-Off Keying
    FSK2 = auto()  # Binary Frequency Shift Key
    BPSK = auto()  # Binary Phase Shift Key
