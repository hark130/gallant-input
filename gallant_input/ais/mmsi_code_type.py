"""Defines the MMSICodeType enum for Maritime Mobile Service Identity (MMSI) code types.

See: https://www.e-navigation.nl/content/mmsi-mid-formats
"""

# Standard Imports
from enum import IntEnum
# Third Party Imports
# Local Imports


class MMSICodeType(IntEnum):
    """Maritime Mobile Service Identity (MMSI) code type."""
    UNDEFINED = 0     # No MMSI code type or undefined
    DIVER = 1         # Diver’s radio (not used in the U.S. in 2013)
    SHIP = 2          # Ship
    GROUP = 3         # Group of ships
    COASTAL = 4       # Coastal stations
    SAR_AIRCRAFT = 5  # SAR (Search and Rescue) aircraft
    NAVIGATION = 6    # Aids to Navigation
    AUXILIARY = 7     # Auxiliary craft associated with a parent ship
    SART = 8          # AIS SART (Search and Rescue Transmitter)
    MOB = 9           # MOB (Man Overboard) device
    EPIRB = 10        # EPIRB (Emergency Position Indicating Radio Beacon) AIS

    @property
    def nice_name(self) -> str:
        """Convert the IntEnum.name into a well-formed string."""
        nice_str = self.name.title().replace('_', ' ')
        return nice_str
