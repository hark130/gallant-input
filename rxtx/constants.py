"""Defines SPOT constants on behalf of the package."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports


##########
# rxtx.* #
##########
# Temporary directory constants
PKG_SHORT_TITLE: Final[str] = 'rxtx'  # Receive/Transmit


###################
# rxtx.arg_parser #
###################
# Arguments
RXTX_CLI_ARG_BAUD_RATE: Final[str] = 'baud'      # Symbol rate
RXTX_CLI_ARG_DEBUG: Final[str] = 'debug'         # Debug behavior
RXTX_CLI_ARG_FILENAME: Final[str] = 'filename'   # Data filename
RXTX_CLI_ARG_SAMP_RATE: Final[str] = 'samprate'  # Sample rate
