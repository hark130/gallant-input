"""Defines the ConfigureDirection Enum for us as a sub-package argument."""

# Standard Imports
from enum import auto, Enum
# Third Party Imports
# Local Imports


class ConfigDirection(Enum):
    """Which direction to configure?"""
    RX = auto()
    TX = auto()
    BOTH = auto()
