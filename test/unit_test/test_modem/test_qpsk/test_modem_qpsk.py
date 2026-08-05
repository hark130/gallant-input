"""Defines the root QPSK() unit test class.

ModemQPSKUnitTest is the parent class for all modem.qpsk QPSK unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_modem.test_modem_qpsk.test_modem_qpsk import ModemQPSKUnitTest

    class ModemSomethingUnitTest(ModemQPSKUnitTest):
        # Establish the local test (input/output) dirs
        def __init__(self, *args, **kwargs) -> None:
        # Default directory for input files
        self.test_input_dir = os.path.join(HERE, 'test_input')
        # Default directory for output files
        self.test_output_dir = os.path.join(HERE, 'test_output')

        # Child class must override this method
        def call_callable(self):
            return my_function(*self._args, **self._kwargs)

        # Child class must override this method
        def validate_return_value(self):
            self._validate_return_value(return_value=return_value)

        # This is your test case
        def test_stuff(self):
            self.set_test_input(1, 2)
            self.expect_return(3)
"""

# Standard Imports
from typing import Any
# Third Party Imports
from test.unit_test.test_modem.test_modem import ModemUnitTest
# Local Imports
from gallant_input.modem.qpsk import QPSK
from gallant_input.modem.qpsk_config import QPSKConfig


class ModemQPSKUnitTest(ModemUnitTest):
    """Parent class for all QPSK method unit tests.

    Inherit from this class, define necessary functionality for the function you're testing and
    be sure to override the following methods in your child class:
        call_callable()
        validate_return_value()

    Available features:
        See: help(TediousUnitTest)

    Attributes:
        test_case_data:   # Stores data about the test case as a TestCaseData object
        test_input_dir:   # Default input directory (OPTIONAL)
        test_output_dir:  # Default output directory (OPTIONAL)
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """ModemQPSKUnitTest ctor."""
        # ATTRIBUTES
        self.input_carr_recover = None  # The optional carrier recovery Config value
        self.input_mapper = None        # The optional mapper Config value
        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # test_obj = self.create_test_obj()
        # return test_obj.the_method_you_are_testing(*self._args, **self._kwargs)
        raise NotImplementedError(
            self._test_error.format('The child class must override the call_callable method with '
                                    'the function to test.'))

    def set_qpsk_ctor_args(self, sample_rate: Any, symbol_rate: Any, carrier_recovery: Any,
                           mapper: Any) -> None:
        """Sets the QPSK() argument values in the test class."""
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.input_carr_recover = carrier_recovery
        self.input_mapper = mapper

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

    def create_test_obj(self) -> QPSK:
        """Create an QPSK() test object.

        Strongly consider calling self.set_qpsk_ctor_args() first.
        """
        # QPSK() ctor argument
        config = QPSKConfig(sample_rate=self.input_sample_rate, symbol_rate=self.input_symbol_rate,
                            carrier_recovery=self.input_carr_recover, mapper=self.input_mapper)
        return QPSK(config=config)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
