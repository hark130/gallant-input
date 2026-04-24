"""Defines the root modem sub-package unit test class.

ModemUnitTest is the parent class for all modem sub-package related unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_modem.test_modem import ModemUnitTest

    class ModemSomethingUnitTest(ModemUnitTest):
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
from test.unit_test.root_unit_test import RootUnitTest
# Local Imports


class ModemUnitTest(RootUnitTest):
    """Parent class for all modem sub-package specific unit tests.

    Inherit from this class, define necessary functionality for the function you're testing and
    be sure to override the following methods in your child class:
        call_callable()
        validate_return_value()

    Available features:
        See: help(TediousUnitTest)

    Attributes:
        test_case_data:    # Stores data about the test case as a TestCaseData object
        test_input_dir:    # Default input directory (OPTIONAL)
        test_output_dir:   # Default output directory (OPTIONAL)
        input_sample_rate  # Test case input: Modem(sample_rate)
        input_symbol_rate  # Test case input: Modem(symbol_rate)
    """

    # REALISTIC BINARY DATA
    # RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO    "
    RDS_SET1_GRP01_MSG00_OFF00 = \
        b'0011011001011000100001101100000000111011001101011000' \
        b'1110000110001000111110011001001011010011111111001100'  # "KO"
    RDS_SET1_GRP02_MSG00_OFF01 = \
        b'0011011001011000100001101100000000111010010110111100' \
        b'1110000110001000111110011001001110010011110001100000'  # "NO"
    RDS_SET1_GRP03_MSG00_OFF02 = \
        b'0011011001011000100001101100000000111010101101110111' \
        b'1110000110001000111110011000100000001000000011011100'  # "  "
    RDS_SET1_GRP04_MSG00_OFF03 = \
        b'0011011001011000100001101100000000111011110110010011' \
        b'1110000110001000111110011000100000001000000011011100'  # "  "
    # RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO    "
    RDS_SET1_MSG00A = RDS_SET1_GRP01_MSG00_OFF00 + RDS_SET1_GRP02_MSG00_OFF01 \
        + RDS_SET1_GRP03_MSG00_OFF02 + RDS_SET1_GRP04_MSG00_OFF03

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """ModemOOKUnitTest ctor."""
        # ATTRIBUTES
        self.input_sample_rate = None
        self.input_symbol_rate = None

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # return the_function_you_are_testing(*self._args, **self._kwargs)
        raise NotImplementedError(
            self._test_error.format('The child class must override the call_callable method with '
                                    'the function to test.'))

    def set_ctor_args(self, sample_rate: Any, symbol_rate: Any) -> None:
        """Sets the Modem() argument values in the test class."""
        self.input_sample_rate = sample_rate
        self.input_symbol_rate = symbol_rate        

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
