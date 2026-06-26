"""Defines the ModScheme IntEnum."""

# Standard Imports
from enum import auto, IntEnum
# Third Party Imports
# Local Imports


class ModScheme(IntEnum):
    """Communicate Radio Data System (RDS) block IDs among the rds sub-package."""
    OOK = auto()
    FSK2 = auto()
    BPSK = auto()
