"""Defines SPOT constants on behalf of the package."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports


###################
# gallant_input.* #
###################
# Temporary directory constants
PKG_SHORT_TITLE: Final[str] = 'gain'  # GALLANT INPUT (GAIN)
# Assumed file extensions
SIGMF_DATA_FILE_EXT: Final[str] = 'sigmf-data'
SIGMF_META_FILE_EXT: Final[str] = 'sigmf-meta'


############################
# gallant_input.arg_parser #
############################
# Parser Destinations
GAIN_CLI_CMD_DEST: Final[str] = 'command'         # ArgumentParser destination for the command
# Commands
GAIN_CLI_CMD_ANALYZE: Final[str] = 'analyze'
GAIN_CLI_CMD_IDENTIFY: Final[str] = 'identify'
# Command Arguments
GAIN_CLI_ARG_DATA_FILE: Final[str] = 'datafile'   # .sigmf-data filename
GAIN_CLI_ARG_META_FILE: Final[str] = 'metafile'   # .sigmf-meta filename
GAIN_CLI_ARG_SIGMF_BASE: Final[str] = 'basename'  # Base filename for .sigmf-* files
# General Arguments
GAIN_CLI_ARG_DEBUG: Final[str] = 'debug'          # Debug logging


######################
# gallant_input.main #
######################
EXIT_CODE_SUCCESS: Final[int] = 0  # Success
EXIT_CODE_INVAL: Final[int] = 1    # Invalid input/environment
EXIT_CODE_ERROR: Final[int] = 2    # Error encountered during execution


######################
# gallant_input.misc #
######################
# Temporary directory constants
TEMP_DIR_DEF_NIX: Final[str] = '/tmp'      # Default *nix temp dir
TEMP_DIR_DEF_WIN: Final[str] = 'C:\\Temp'  # Default Windows temp dir
