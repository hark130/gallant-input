"""Defines the ManchesterVerdict IntEnum."""

# Standard Imports
from enum import auto, IntEnum
# Third Party Imports
# Local Imports


class ManchesterVerdict(IntEnum):
    """Communicates whether a symbol stream appears to be Manchester coded."""
    INCONCLUSIVE = auto()    # Not enough (or ambiguous) evidence
    MANCHESTER = auto()      # Manchester family (plain or differential)
    NOT_MANCHESTER = auto()  # Evidence rules out Manchester coding
