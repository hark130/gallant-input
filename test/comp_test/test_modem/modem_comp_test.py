"""Defines the base GAIN modem module Component Test Class.

Import ModemCompTest for more details and usage instructions.

    Typical usage example:

    from test.comp_test.modem_comp_test import ModemCompTest

    class OOKModemCompTest(ModemCompTest):
        def __init__(self, *args, **kwargs) -> None:
            ...
"""

# Standard Imports
from typing import Any
# Third Party Imports
# Local Imports
from test.base_unit_test import BaseUnitTest


class ModemCompTest(BaseUnitTest):
    """GAIN.modem component test class.

    Defines functionality needed to run component tests on the modem sub-package.
    Inheriting from TediousUnitTest to make use of the 'callable' functionality (since we'll
    likely just be comparing modulate() calls to demodulate() and vice-versa).
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # return the_function_you_are_testing(*self._args, **self._kwargs)
        raise NotImplementedError(
            self._test_error.format('The child class must override the call_callable method with '
                                    'the function to test.'))

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call.

        Child class must override this method.
        See TediousUnitTest.validate_return_value() for details.
        """
        # Example Usage:
        # self._validate_return_value(return_value=return_value)
        raise NotImplementedError(
            self._test_error.format('The child class must override the validate_return_value '
                                    'method with the appropriate validation logic'))

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
