"""Parse the command line arguments on behalf of the package."""
# Standard Imports
from argparse import _SubParsersAction as SubParsersAction
from typing import Any
import argparse
import os
# Third Party Imports
# Local Imports
from gallant_input.argvals import ArgVals
from gallant_input.constants import (GAIN_CLI_ARG_DATA_FILE, GAIN_CLI_ARG_DEBUG,
                                     GAIN_CLI_ARG_META_FILE, GAIN_CLI_ARG_SIGMF_BASE,
                                     GAIN_CLI_CMD_ANALYZE, GAIN_CLI_CMD_DEST, PKG_SHORT_TITLE,
                                     SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT)
from gallant_input.misc import determine_tmp_dir
from gallant_input.validation import validate_type


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
    parser = argparse.ArgumentParser(prog=PKG_SHORT_TITLE,
                                     description='Gallant Input (GAIN): Processing RF captures.')
    subparsers = parser.add_subparsers(dest=GAIN_CLI_CMD_DEST, help='Processing feature')
    _add_analyze_cmd(subparser=subparsers)
    parser.add_argument(f'--{GAIN_CLI_ARG_DEBUG}', action='store_true',
                        help=f'Log debug messages to "{debug_log}"', required=False)

    # PARSE IT
    args = parser.parse_args()

    # DONE
    return _construct_arg_vals(args=args)


def _add_analyze_cmd(subparser: SubParsersAction) -> None:
    """Add the analyze command subparser."""
    # LOCAL VARIABLES
    analyze_parser = None  # Analyze command subparser

    # INPUT VALIDATION
    validate_type(var=subparser, var_name='subparser', var_type=SubParsersAction)

    # ADD IT
    analyze_parser = subparser.add_parser(GAIN_CLI_CMD_ANALYZE, help='Analyze a SigMF capture')
    _add_sigmf_args(parser=analyze_parser)


def _add_sigmf_args(parser: argparse.ArgumentParser) -> None:
    """Add the standard SigMF arguments to the parser: data, meta, base."""
    # INPUT VALIDATION
    validate_type(var=parser, var_name='parser', var_type=argparse.ArgumentParser)

    # ADD IT
    parser.add_argument(f'-{GAIN_CLI_ARG_DATA_FILE[0]}', f'--{GAIN_CLI_ARG_DATA_FILE}',
                        action='store', help='The SigMF data filename (also use '
                                             f'--{GAIN_CLI_ARG_META_FILE})')
    parser.add_argument(f'-{GAIN_CLI_ARG_META_FILE[0]}', f'--{GAIN_CLI_ARG_META_FILE}',
                        action='store', help='The SigMF data filename (also use '
                                             f'--{GAIN_CLI_ARG_DATA_FILE})')
    parser.add_argument(f'-{GAIN_CLI_ARG_SIGMF_BASE[0]}', f'--{GAIN_CLI_ARG_SIGMF_BASE}',
                        action='store', help='Base filename for the SigMF data and meta files '
                                             f'(replaces --{GAIN_CLI_ARG_DATA_FILE} and '
                                             f'--{GAIN_CLI_ARG_META_FILE})')


def _construct_arg_vals(args: argparse.Namespace) -> ArgVals:
    """Construct an ArgVals data class from the parsed args."""
    # LOCAL VARIABLES
    command = None    # args.GAIN_CLI_CMD_DEST
    debug = None      # args.GAIN_CLI_ARG_DEBUG
    data_file = None  # args.GAIN_CLI_ARG_DATA_FILE
    meta_file = None  # args.GAIN_CLI_ARG_META_FILE
    base_name = None  # args.GAIN_CLI_ARG_SIGMF_BASE

    # INPUT VALIDATION
    validate_type(var=args, var_name='args', var_type=argparse.Namespace)

    # GET IT
    command = _get_eafp_attr(args=args, attr=GAIN_CLI_CMD_DEST)
    debug = _get_eafp_attr(args=args, attr=GAIN_CLI_ARG_DEBUG)
    data_file = _get_eafp_attr(args=args, attr=GAIN_CLI_ARG_DATA_FILE)
    meta_file = _get_eafp_attr(args=args, attr=GAIN_CLI_ARG_META_FILE)
    base_name = _get_eafp_attr(args=args, attr=GAIN_CLI_ARG_SIGMF_BASE)

    # VALIDATE
    data_file, meta_file = _validate_mutex_args(data_file, meta_file, base_name)

    # DONE
    return ArgVals(command=command, debug=debug, data_file=data_file, meta_file=meta_file)


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


def _validate_mutex_args(data_file: str, meta_file: str, base_name: str) -> tuple[str, str]:
    """Validate mutually exclusive command arguments.

    (date_file && metafile) != (base_name)

    Returns:
        A tuple containing the data_file and meta_file names.  Value will be either the
        validated originals or valid file extensions appended to base_name.

    Raises:
        argparse.ArgumentTypeError: Mutex argument violation.
    """
    # LOCAL VARIABLES
    dfile = data_file  # SigMF Data filename
    mfile = meta_file  # SigMF Meta filename

    # VALIDATE IT
    # data_file != meta_file
    if isinstance(data_file, str) != isinstance(meta_file, str):
        raise argparse.ArgumentTypeError('If either is provided, then both '
                                         f'"--{GAIN_CLI_ARG_DATA_FILE}" AND '
                                         f'"--{GAIN_CLI_ARG_META_FILE}" must be provided')
    if data_file is None and meta_file is None:
        if not base_name:
            raise argparse.ArgumentTypeError(f'Either "--{GAIN_CLI_ARG_DATA_FILE}" AND '
                                             f'"--{GAIN_CLI_ARG_META_FILE}" must be used or '
                                             f'"--{GAIN_CLI_ARG_SIGMF_BASE}" must be provided')
        else:
            dfile = base_name + f'.{SIGMF_DATA_FILE_EXT}'
            mfile = base_name + f'.{SIGMF_META_FILE_EXT}'
    else:
        if base_name is not None:
            raise argparse.ArgumentTypeError(f'Do not provide "--{GAIN_CLI_ARG_SIGMF_BASE}" when '
                                             f'using "--{GAIN_CLI_ARG_DATA_FILE}" AND '
                                             f'"--{GAIN_CLI_ARG_META_FILE}"')

    # DONE
    return tuple((dfile, mfile))
