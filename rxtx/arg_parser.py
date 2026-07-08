"""Parse the command line arguments on behalf of the package."""
# Standard Imports
from typing import Any
import argparse
import os
# Third Party Imports
# Local Imports
from gallant_input.validation import (validate_bool, validate_pos_float_or_int, validate_string,
                                      validate_type)
from rxtx.argvals import ArgVals
from rxtx.constants import (PKG_SHORT_TITLE, RXTX_CLI_ARG_BAUD_RATE, RXTX_CLI_ARG_DEBUG,
                            RXTX_CLI_ARG_FILENAME, RXTX_CLI_ARG_SAMP_RATE)


def parse_args() -> ArgVals:
    """Parse the command line arguments.

    Returns:
        An ArgVals data class containing all parsed values.
    """
    # LOCAL VARIABLES
    parser = _create_parser()  # ArgumentParser object
    args = None                # Parsed argument Namespace
    arg_vals = None            # ArgVals object

    # PARSE IT
    args = parser.parse_args()
    arg_vals = _construct_arg_vals(args=args)
    _validate_arg_vals(arg_vals=arg_vals)

    # DONE
    return arg_vals


def print_help() -> None:
    """Print the help."""
    parser = _create_parser()  # ArgumentParser object
    parser.print_help()


def _create_parser() -> argparse.ArgumentParser:
    """SPOT to create the argument parser."""
    parser = argparse.ArgumentParser(description='Static Receiver/Transmitters.')
    parser.add_argument(f'--{RXTX_CLI_ARG_DEBUG}', action='store_true',
                        help=f'Allow exception traceback on error', required=False)
    parser.add_argument(f'-{RXTX_CLI_ARG_FILENAME[0]}', f'--{RXTX_CLI_ARG_FILENAME}',
                        action='store', help='The data filename to read samples from')
    parser.add_argument(f'-{RXTX_CLI_ARG_BAUD_RATE[0]}', f'--{RXTX_CLI_ARG_BAUD_RATE}',
                        action='store', help='Baud rate (AKA symbol rate)')
    parser.add_argument(f'-{RXTX_CLI_ARG_SAMP_RATE[0]}', f'--{RXTX_CLI_ARG_SAMP_RATE}',
                        action='store', required=False,
                        help='Sample rate (Hz); Mandatory for missing SigMF metadata')
    return parser


def _construct_arg_vals(args: argparse.Namespace) -> ArgVals:
    """Construct an ArgVals data class from the parsed args."""
    # LOCAL VARIABLES
    baud_rate = None  # args.RXTX_CLI_ARG_BAUD_RATE
    debug = None      # args.RXTX_CLI_ARG_DEBUG
    filename = None   # args.RXTX_CLI_ARG_FILENAME
    samp_rate = None  # args.RXTX_CLI_ARG_SAMP_RATE

    # INPUT VALIDATION
    validate_type(var=args, var_name='args', var_type=argparse.Namespace)

    # GET IT
    baud_rate = _get_eafp_number(args=args, attr=RXTX_CLI_ARG_BAUD_RATE)
    debug = _get_eafp_bool(args=args, attr=RXTX_CLI_ARG_DEBUG)
    filename = _get_eafp_attr(args=args, attr=RXTX_CLI_ARG_FILENAME)
    samp_rate = _get_eafp_number(args=args, attr=RXTX_CLI_ARG_SAMP_RATE)

    # DONE
    return ArgVals(filename=filename, debug=debug, sample_rate=samp_rate, symbol_rate=baud_rate)


def _convert_str_to_num(value: str) -> float | int:
    number = float(value)
    return int(number) if number.is_integer() else number


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


def _get_eafp_bool(args: argparse.Namespace, attr: str) -> bool:
    """Safely retrieve a boolean value."""
    # LOCAL VARIABLES
    result = False  # Translated value
    value = False   # Retrieved value

    # GET IT
    try:
        value = getattr(args, attr)
        if value:
            result = True
    except AttributeError:
        pass  # Easier to ask for forgiveness than permission (EAFP)

    # DONE
    return result


def _get_eafp_number(args: argparse.Namespace, attr: str) -> float | int:
    """Safely retrieve a numerical value."""
    # LOCAL VARIABLES
    result = None  # Converted number
    value = False  # Retrieved value

    # GET IT
    try:
        value = getattr(args, attr)
        if value:
            result = _convert_str_to_num(value)
    except AttributeError:
        pass  # Easier to ask for forgiveness than permission (EAFP)

    # DONE
    return result

def _validate_arg_vals(arg_vals: ArgVals) -> None:
    """Validate the results."""
    validate_type(arg_vals, 'arg_vals', ArgVals)
    validate_string(arg_vals.filename, f'--{RXTX_CLI_ARG_FILENAME}', can_be_empty=False)
    validate_bool(arg_vals.debug, f'--{RXTX_CLI_ARG_DEBUG}')
    validate_pos_float_or_int(arg_vals.symbol_rate, f'--{RXTX_CLI_ARG_BAUD_RATE}')
    if arg_vals.sample_rate is not None:
        validate_pos_float_or_int(arg_vals.sample_rate, f'--{RXTX_CLI_ARG_SAMP_RATE}')
