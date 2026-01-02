"""Defines the RBDSProgramType enum for Radio Broadcast Data System (RBDS) Program Type (PTY) codes.

Not to be confused with Radio Data System (RDS) PTY codes.
Read 'RDS: The Radio Data System' Chapter 2 'Differences Between RDS and RBDS' here:
https://www.iz3mez.it/wp-content/library/ebook/RDS%20-%20The%20Radio%20Data%20System.pdf
"""

# Standard Imports
from enum import IntEnum
# Third Party Imports
# Local Imports


class RBDSProgTypeCode(IntEnum):
    """Radio Broadcast Data System (RBDS) Program Type (PTY) code."""
    UNDEFINED = 0               # No programme type or undefined 
    NEWS = 1                    # News
    INFORMATION = 2             # Information 
    SPORTS = 3                  # Sports 
    TALK = 4                    # Talk 
    ROCK = 5                    # Rock 
    CLASSIC_ROCK = 6            # Classic rock 
    ADULT_HITS = 7              # Adult hits 
    SOFT_ROCK = 8               # Soft rock 
    TOP_40 = 9                  # Top 40 
    COUNTRY = 10                # Country 
    OLDIES = 11                 # Oldies 
    SOFT_MUSIC = 12             # Soft music 
    NOSTALGIA = 13              # Nostalgia 
    JAZZ = 14                   # Jazz 
    CLASSICAL = 15              # Classical 
    RHYTHM_AND_BLUES = 16       # Rhythm and blues 
    SOFT_RHYTHM_AND_BLUES = 17  # Soft rhythm and blues 
    LANGUAGE = 18               # Language 
    RELIGIOUS_MUSIC = 19        # Religious music 
    RELIGIOUS_TALK = 20         # Religious talk 
    PERSONALITY = 21            # Personality 
    PUBLIC = 22                 # Public 
    COLLEGE = 23                # College 
    SPANISH_TALK = 24           # Spanish Talk 
    SPANISH_MUSIC = 25          # Spanish Music 
    HIP_HOP = 26                # Hip hop 
    UNASSIGNED27 = 27           # Unassigned27
    UNASSIGNED28 = 28           # Unassigned28
    WEATHER = 29                # Weather 
    EMERGENCY_TEST = 30         # Emergency test 
    EMERGENCY = 31              # Emergency

    @property
    def nice_name(self) -> str:
        """Convert the IntEnum.name into a well-formed string."""
        nice_str = self.name.title().replace('_', ' ')
        nice_str = nice_str.replace('AND'.title(), 'AND'.lower())  # Special Case
        return nice_str
