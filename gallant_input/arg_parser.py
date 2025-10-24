"""Parse the command line arguments on behalf of the package."""
# Standard Imports
from typing import Any
import argparse
import os
# Third Party Imports
# Local Imports
from gallant_input.argvals import ArgVals
from gallant_input.misc import determine_tmp_dir


def parse_args() -> ArgVals:
    """Parse the command line arguments.

    Returns:
        An ArgVals data class containing all parsed values.
    """
    # LOCAL VARIABLES
    parser = None                                   # ArgumentParser object
    subparsers = None                               # Subparsers
    args = None                                     # Parsed argument Namespace
    # Debug log location
    debug_log = os.path.join(determine_tmp_dir(), f'{PKG_SHORT_TITLE}_YYYYMMDD_HHMMSS-#.log')

    # SETUP
    jitb_games.sort()
    parser = argparse.ArgumentParser(prog=PKG_SHORT_TITLE,
                                     description='Jack in the Box (JITB): Connecting Jackbox '
                                                 'Games to the OpenAI API.  JITB currently '
                                                 f'supports: {", ".join(jitb_games)}.')
    subparsers = parser.add_subparsers(dest='command', help='Login support: automatic or manual')
    _add_analyze_cmd(subparser=subparsers)
    parser.add_argument(f'--{GAIN_CLI_ARG_DEBUG}', action='store_true',
                        help=f'Log debug messages to "{debug_log}"', required=False)

    # PARSE IT
    args = parser.parse_args()

    # DONE
    return None  # TODO... CHANGE THIS TO RETURN an ArgVals() OBJECT!


def _add_analyze_cmd(subparser: argparse._SubParsersAction) -> None:
    """Add the analyze command subparser."""
    # LOCAL VARIABLES
    analyze_parser = None  # Analyze command subparser

    # INPUT VALIDATION
    validate_type(var=subparser, var_name='subparser', var_type=argparse._SubParsersAction)

    # ADD IT
    analyze_parser = subparser.add_parser(GAIN_CLI_CMD_ANALYZE, help='Analyze a SigMF capture')
    analyze_parser.add_argument(f'-{GAIN_CLI_ARG_DATA_FILE[0]}', f'--{GAIN_CLI_ARG_DATA_FILE}',
                                action='store',
                                help='The SigMF data filename (also use '
                                     f'--{GAIN_CLI_ARG_META_FILE})')
    analyze_parser.add_argument(f'-{GAIN_CLI_ARG_META_FILE[0]}', f'--{GAIN_CLI_ARG_META_FILE}',
                                action='store',
                                help='The SigMF data filename (also use '
                                     f'--{GAIN_CLI_ARG_DATA_FILE})')
    analyze_parser.add_argument(f'-{GAIN_CLI_ARG_SIGMF_BASE[0]}', f'--{GAIN_CLI_ARG_SIGMF_BASE}',
                                action='store',
                                help='Base filename for the SigMF data and meta files '
                                     f'(replaces --{GAIN_CLI_ARG_DATA_FILE} and '
                                     f'--{GAIN_CLI_ARG_META_FILE})')


def _get_eafp_attr(args: argparse.Namespace, attr: str) -> Any:
    """Safely retrieve values from a Namespace (if they exist)."""
    # LOCAL VARIABLES
    value = None  # Retrieved value

    # GET IT
    try:
        value = getattr(args, attr)
    except AttributeError:
        pass  # Easier to ask for forgiveness than permission (EAFP)

    # DONE
    return value
