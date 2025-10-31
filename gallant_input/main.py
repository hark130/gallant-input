"""Entry level function."""

# Standard Imports
from pathlib import Path
# Third Party Imports
# Local Imports
from gallant_input.arg_parser import parse_args
from gallant_input.logger import log_exception, Logger
from gallant_input.sigmfmetaparser import SigMFMetaParser
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
    data_file = None                     # Data filename parsed from CLI args
    meta_file = None                     # Meta filename parsed from CLI args
    meta_parser = None                   # SigMFMetaParser object

    # 1. PREPARATION
    try:
        # PARSE IT
        argvals = parse_args()

        # SETUP
        Logger.initialize(debugging=argvals.debug)

        # ENVIRONMENT VALIDATION
        data_file = Path(argvals.data_file)
        meta_file = Path(argvals.meta_file)
        validate_file(validate_this=data_file, param_name=f'--{const.GAIN_CLI_ARG_DATA_FILE}',
                      must_exist=True)
        validate_file(validate_this=meta_file, param_name=f'--{const.GAIN_CLI_ARG_META_FILE}',
                      must_exist=True)
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
                    meta_parser = SigMFMetaParser(meta_filename=meta_file)
                    print(f'Center Frequency: {meta_parser.get_center_freq()}hz')
                # identify
                case const.GAIN_CLI_CMD_IDENTIFY:
                    Logger.info('Executing identification...')
                    raise NotImplementedError(f'Command "{argvals.command}" is not yet '
                                              'implemented (see: GAIN-6)')
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
