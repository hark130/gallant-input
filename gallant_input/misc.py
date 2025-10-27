"""Miscellaneous functionality that doesn't warrant its own module.

    Typical usage example:

    from gallant_input.misc import determine_tmp_dir

    print(f'Store temporary log files in the "{determine_tmp_dir()}" directory.')
"""
# Standard Imports
import sys
# Third Party Imports
# Local Imports
from gallant_input.constants import TEMP_DIR_DEF_NIX, TEMP_DIR_DEF_WIN


def determine_tmp_dir() -> str:
    """Determine the temporary directory in which to store --debug log files.

    Hard-coded results:
        - /tmp for *nix
        - C:\\Temp for Windows

    Returns:
        A string representing the temporary directory to use for the debug log files.

    Raises:
        RuntimeError: Unable to determine the platform type.
    """
    # LOCAL VARIABLES
    tmp_dir = None           # Temporary directory
    platform = sys.platform  # The system platform

    # VALIDATE
    if platform.lower() in ('cygwin', 'darwin', 'linux', 'linux2'):
        tmp_dir = TEMP_DIR_DEF_NIX
    elif platform.lower() == 'win32':
        tmp_dir = TEMP_DIR_DEF_WIN
    else:
        raise RuntimeError('Unable to determine host OS from '
                           f'"{platform}" to ascertain the temporary directory.')

    # DONE
    return tmp_dir
