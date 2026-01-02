"""Defines the RDSProgramType enum for RDS Program Type (PTY) codes.

Not to be confused with Radio Broadcast Data System (RBDS) PTY codes.
Read 'RDS: The Radio Data System' Chapter 2 'Differences Between RDS and RBDS' here:
https://www.iz3mez.it/wp-content/library/ebook/RDS%20-%20The%20Radio%20Data%20System.pdf
"""

# Standard Imports
from enum import IntEnum
# Third Party Imports
# Local Imports


class RDSProgTypeCode(IntEnum):
    """RDS Program Type (PTY) code."""
    UNDEFINED = 0            # No programme type or undefined 
    NEWS = 1                 # News
    CURRENT_AFFAIRS = 2      # Current affairs
    INFORMATION = 3          # Information
    SPORT = 4                # Sport
    EDUCATION = 5            # Education
    DRAMA = 6                # Drama
    CULTURE = 7              # Culture
    SCIENCE = 8              # Science
    VARIED = 9               # Varied
    POP_MUSIC = 10           # Pop music
    ROCK_MUSIC = 11          # Rock music
    EASY_LISTENING = 12      # Easy listening
    LIGHT_CLASSICAL = 13     # Light classical
    SERIOUS_CLASSICAL = 14   # Serious classical
    OTHER_MUSIC = 15         # Other music
    WEATHER = 16             # Weather
    FINANCE = 17             # Finance
    CHILDRENS_PROGRAMS = 18  # Children's programmes
    SOCIAL_AFFAIRS = 19      # Social affairs
    RELIGION = 20            # Religion
    PHONE_IN = 21            # Phone-in
    TRAVEL = 22              # Travel
    LEISURE = 23             # Leisure
    JAZZ_MUSIC = 24          # Jazz music
    COUNTRY_MUSCI = 25       # Country music
    NATIONAL_MUSIC = 26      # National music
    OLDIES_MUSIC = 27        # Oldies music
    FOLK_MUSIC = 28          # Folk music 
    DOCUMENTARY = 29         # Documentary
    ALARM_TEST = 30          # Alarm test
    ALARM = 31               # Alarm

    @property
    def nice_name(self) -> str:
        """Convert the IntEnum.name into a well-formed string."""
        nice_str = self.name.replace('CHILDRENS', "CHILDREN'S")  # Special Case
        nice_str = nice_str.title().replace('_', ' ')
        return nice_str
