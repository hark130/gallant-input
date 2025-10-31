"""Entry level function."""

# Standard Imports
from pathlib import Path
# Third Party Imports
# Local Imports
from gallant_input.arg_parser import parse_args
from gallant_input.logger import log_exception, Logger
from gallant_input.validation import validate_file
import gallant_input.constants as const


# pylint: disable=broad-exception-caught
def main() -> int:
    """Entry level function: parse args, initialize the logger, respond to commands.

    Returns:
        An integer to be used as an exit code (see: gallant_input.constants).

    Raises:
        All raised exceptions are caught, logged, and then this function immediately returns.
    """
    # LOCAL VARIABLES
    exit_code = const.EXIT_CODE_SUCCESS  # Return value
    argvals = None                       # ArgVals data class w/ parsed args

    # 1. PREPARATION
    try:
        # PARSE IT
        argvals = parse_args()

        # SETUP
        Logger.initialize(debugging=argvals.debug)

        # ENVIRONMENT VALIDATION
        validate_file(validate_this=Path(argvals.data_file),
                      param_name=f'--{const.GAIN_CLI_ARG_DATA_FILE}', must_exist=True)
        validate_file(validate_this=Path(argvals.meta_file),
                      param_name=f'--{const.GAIN_CLI_ARG_META_FILE}', must_exist=True)
    except Exception as err:
        log_exception(error=err)
        exit_code = const.EXIT_CODE_INVAL
    # 2. EXECUTION
    else:
        try:
            # RUN IT
            match argvals.command:
                # analyze
                case const.GAIN_CLI_CMD_ANALYZE:
                    Logger.info('Executing analysis...')
                # identify
                case const.GAIN_CLI_CMD_IDENTIFY:
                    Logger.info('Executing identification...')
                # ???
                case _:
                    raise NotImplementedError(f'Command "{argvals.command}" passed validation '
                                              'but is not supported')
        except Exception as err:
            log_exception(error=err)
            exit_code = const.EXIT_CODE_ERROR

    # 3. DONE
    try:
        Logger.shutdown()
    except Exception as err:
        log_exception(error=err)
        if const.EXIT_CODE_SUCCESS == exit_code:
            exit_code = const.EXIT_CODE_ERROR
    return exit_code
