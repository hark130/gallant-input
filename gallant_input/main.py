"""Entry level function."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.arg_parser import parse_args
from gallant_input.constants import EXIT_CODE_SUCCESS
from gallant_input.logger import Logger


def main() -> int:
    """Entry level function: parse args, initialize the logger, respond to commands.

    Returns:
        An integer to be used as an exit code (see: gallant_input.constants).

    Raises:
        All raised exceptions are caught, logged, and then this function immediately returns.
    """
    # LOCAL VARIABLES
    exit_code = EXIT_CODE_SUCCESS  # Return value
    argvals = None                 # ArgVals data class w/ parsed args

    # INPUT VALIDATION

    # PARSE IT
    argvals = parse_args()
    print(f'COMMAND: {argvals.command}')  # DEBUGGING
    print(f'DEBUG: {argvals.debug}')  # DEBUGGING
    print(f'DATA FILE: {argvals.data_file}')  # DEBUGGING
    print(f'META FILE: {argvals.meta_file}')  # DEBUGGING

    # SETUP
    Logger.initialize(debugging=argvals.debug)

    # ENVIRONMENT VALIDATION
    Logger.info('INFO')  # DEBUGGING
    Logger.debug('DEBUG?')  # DEBUGGING
    Logger.error('ERROR!')  # DEBUGGING

    # RUN IT

    # DONE
    Logger.shutdown()
    return exit_code
