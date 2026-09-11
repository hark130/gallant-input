"""Defines the root FSK2() unit test class.

ModemFSK2UnitTest is the parent class for all modem.fsk2 FSK2 unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_modem.test_modem_fsk2.test_modem_fsk2 import ModemFSK2UnitTest

    class ModemSomethingUnitTest(ModemFSK2UnitTest):
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
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config


class ModemFSK2UnitTest(ModemUnitTest):
    """Parent class for all FSK2 method unit tests.

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
        """ModemFSK2UnitTest ctor."""
        # ATTRIBUTES
        self.input_freq0 = None  # Test case input: freq0
        self.input_freq1 = None  # Test case input: freq1
        self.input_phase = None  # Test case input: phase
        self._demod = False      # Default mod/demod test state

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # test_obj = FSK2(self.input_modem_fsk2)
        # return test_obj.the_method_you_are_testing(*self._args, **self._kwargs)
        raise NotImplementedError(
            self._test_error.format('The child class must override the call_callable method with '
                                    'the function to test.'))

# Leave me be, Pylint
# pylint: disable = too-many-arguments, too-many-positional-arguments
    def set_fsk2_ctor_args(self, sample_rate: Any, symbol_rate: Any, freq0: Any, freq1: Any,
                           phase: Any) -> None:
        """Sets the FSK2() argument values in the test class."""
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.input_freq0 = freq0
        self.input_freq1 = freq1
        self.input_phase = phase

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
# pylint: enable = too-many-arguments, too-many-positional-arguments

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def create_test_obj(self) -> FSK2:
        """Create an FSK2() test object.

        Strongly consider calling self.set_fsk2_ctor_args() first.
        """
        config = None  # FSK2() ctor argument
        self._validate_type(self._demod, '_demod instance attribute', bool)
        config = FSK2Config(sample_rate=self.input_sample_rate,
                            symbol_rate=self.input_symbol_rate,
                            freq0=self.input_freq0, freq1=self.input_freq1,
                            phase=self.input_phase)
        config.set_demod(demod=self._demod)
        return FSK2(config=config)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
