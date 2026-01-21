"""Defines the root ais sub-package unit test class.

AISUnitTest is the parent class for all ais sub-package related unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_ais.test_ais import AISUnitTest

    class AISSomethingUnitTest(AISUnitTest):
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
from gallant_input.ais.payload import AISPayload


class AISUnitTest(RootUnitTest):
    """Parent class for all ais sub-package specific unit tests.

    Inherit from this class, define necessary functionality for the function you're testing and
    be sure to override the following methods in your child class:
        call_callable()
        validate_return_value()

    Available features:
        See: help(TediousUnitTest)

    Attributes:
        input_ap_bin_bytes:  # Test case input: AISPayload(bin_bytes)
        test_case_data:      # Stores data about the test case as a TestCaseData object
        test_input_dir:      # Default input directory (OPTIONAL)
        test_output_dir:     # Default output directory (OPTIONAL)
    """

    # KNOWN GOOD BLOCK VALUES
    # Generated using https://github.com/trendmicro/ais/tree/master
    # python AIVDM_Encoder.py --type=1 --vsize=30x10
    # Values = {MSG TYPE: 1, MMSI: 247320162 (MID: 247), REPEAT: 0}
    GOOD_AIS_PAYLOAD1 = b'000001000011101011110111001110011000101111' \
                        + b'100000000000000001000000101100100000101101' \
                        + b'000110011010001001010000010100100011010000' \
                        + b'101111111111001100000000000000000000000000'

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """AISUnitTest ctor."""
        # ATTRIBUTES
        self.input_ap_bin_bytes = None  # Test case input: AISPayload(bin_bytes)

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

    def create_aispayload(self, bin_bytes: Any) -> AISPayload:
        """Set the AISPayload ctor arguments and create the object.

        Args:
            bin_bytes: Sets the bin_bytes argument input.
                Accepts any input, including bad input.
        """
        self.set_aispayload_ctor_args(bin_bytes=bin_bytes)  # Set the arguments
        return self._create_aispayload()  # Create the object

    def set_aispayload_ctor_args(self, bin_bytes: Any) -> None:
        """Set the AISPayload() class ctor arguments.

        Args:
            bin_bytes: Sets the bin_bytes argument input.
                Accepts any input, including bad input.
        """
        self.input_ap_bin_bytes = bin_bytes

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _create_aispayload(self) -> AISPayload:
        """Create an AISPayload object using attribute values."""
        return AISPayload(self.input_ap_bin_bytes)
