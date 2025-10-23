"""Defines the root GAIN Component Test Class.

Import RootCompTest for more details and usage instructions.

    Typical usage example:

    from test.comp_test.root_comp_test import RootCompTest

    class GainCompTest(RootCompTest):
        def __init__(self, *args, **kwargs) -> None:
            ...

    Environment variable usage:

    # GENERATING REPORT OUTPUT
    > export TEDIOUS_START_VERBOSE_OVERRIDE=True      # Use this to set verbosity to ALL
    > python -m test.comp_test                        # Executes all functional test cases
    > unset TEDIOUS_START_VERBOSE_OVERRIDE            # Unset it to "clean" your environment
"""

# Standard Imports
from typing import Any
# Third Party Imports
# Local Imports
from test.root_func_test import RootFuncTest


class RootCompTest(RootFuncTest):
    """GAIN component test class.

    Defines functionality needed by all of this project's component tests.
    """

    # CORE CLASS METHODS
    # Methods listed in call order
    def validate_results(self) -> Any:
        """Verify results of execution."""
        raise NotImplementedError(
            self._test_error.format('The child class must override the validate_results method'))

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
