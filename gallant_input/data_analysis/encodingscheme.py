"""Defines the EncodingScheme IntEnum."""

# Standard Imports
from enum import auto, IntEnum
# Third Party Imports
# Local Imports


class EncodingScheme(IntEnum):
    """Communicates the line coding (AKA encoding scheme) believed to be in a symbol stream."""
    UNKNOWN = auto()          # Not enough evidence to say
    NRZ = auto()              # Non-Return-to-Zero: the symbol is the bit
    NRZI = auto()             # Non-Return-to-Zero Inverted: a change in level carries the bit
    MANCHESTER = auto()       # Two chips per bit, always a mid-bit transition
    DIFF_MANCHESTER = auto()  # Manchester chips, but bit boundary transitions carry the bit
    OVERSAMPLED_NRZ = auto()  # Each NRZ symbol was read twice (symbol rate set 2x too high)
