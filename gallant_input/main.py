"""Entry level function."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.arg_parser import parse_args
from gallant_input.constants import EXIT_CODE_ERROR, EXIT_CODE_INVAL, EXIT_CODE_SUCCESS
from gallant_input.logger import log_exception, Logger


# pylint: disable=broad-exception-caught
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

    # 1. PREPARATION
    try:
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
    except Exception as err:
        log_exception(error=err)
        exit_code = EXIT_CODE_INVAL
    # 2. EXECUTION
    else:
        try:
            # RUN IT
            pass  # TODO
        except Exception as err:
            log_exception(error=err)
            exit_code = EXIT_CODE_ERROR

    # 3. DONE
    try:
        Logger.shutdown()
    except Exception as err:
        log_exception(error=err)
        if EXIT_CODE_SUCCESS == exit_code:
            exit_code = EXIT_CODE_ERROR
    return exit_code
