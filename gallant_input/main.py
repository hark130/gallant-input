"""Entry level function."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.constants import EXIT_CODE_SUCCESS


def main() -> int:
    """Entry level function: parse args, initialize the logger, respond to commands.

    Returns:
        An integer to be used as an exit code (see: gallant_input.constants).

    Raises:
        All raised exceptions are caught, logged, and then this function immediately returns.
    """
    # LOCAL VARIABLES
    exit_code = EXIT_CODE_SUCCESS  # Return value

    # INPUT VALIDATION

    # PARSE IT

    # ENVIRONMENT VALIDATION

    # RUN IT

    # DONE
    return exit_code
