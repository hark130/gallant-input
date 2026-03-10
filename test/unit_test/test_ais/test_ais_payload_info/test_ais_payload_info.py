"""Defines the root AISPayloadInfo unit test class.

AISPayloadInfoUnitTest is the parent class for all ais.block AISPayloadInfo unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_ais.test_ais_block.test_ais_block import AISPayloadInfoUnitTest

    class AISSomethingUnitTest(AISPayloadInfoUnitTest):
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
from test.unit_test.test_ais.test_ais import AISUnitTest
# Local Imports
from gallant_input.ais.payload_info import AISPayloadInfo
from gallant_input.validation import validate_bytes


class AISPayloadInfoUnitTest(AISUnitTest):
    """Parent class for all AISPayloadInfo method unit tests.

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

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # test_obj = AISPayloadInfo(...)
        # return test_obj.the_method_you_are_testing(*self._args, **self._kwargs)
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

    def create_aispayloadinfo(self, in_bytes: bytes) -> AISPayloadInfo:
        """Create an AISPayloadInfo obj using a binary bytes object.

        Args:
            in_bytes: A bytes object, binary or otherwise, of minimum length 38 to create the
                object with.  Data does not have to be valid.
        """
        validate_bytes(in_bytes, 'in_bytes')
        if len(in_bytes) < 38:
            self.fail_test_case('This method requires "in_bytes" to be of minimum length 38 '
                                f'instead of length {len(in_bytes)}')
        return self.create_aispayloadinfo_args(
                msg_type=in_bytes[0:6], repeat=in_bytes[6:8],
                mmsi=in_bytes[8:38], msg_bits=in_bytes[38:]
            )

    def create_aispayloadinfo_args(self, msg_type: Any, repeat: Any,
                                   mmsi: Any, msg_bits: Any) -> AISPayloadInfo:
        """Create an AISPayloadInfo obj using attribute values.

        Args:
            msg_type: Intended to be Message Type [6 bits] but may be anything.
            repeat: Intended to be Repeat Indicator [2 bits] but may be anything.
            mmsi: Intended to be Maritime Mobile Service Identity (MMSI) [30 bits]
                but may be anything.
            msg_bits: Intended to be Message Type specific fields [...] but may be anything.
        """
        # LOCAL VARIABLES
        api_obj = None  # The AISPayloadInfo object

        # CREATE IT (w/ args)
        try:
            api_obj = AISPayloadInfo(msg_type=msg_type, repeat=repeat, mmsi=mmsi, msg_bits=msg_bits)
        # NameError: Not defined
        # ImportError: Not imported(?!)
        # TypeError: Missing required argument, unexpected keyword argument, too many arguments
        except (NameError, ImportError, TypeError) as err:
            self.fail_test_case(f'Failed to create an AISPayloadInfo() object with: {repr(err)}')

        # DONE
        return api_obj

    def get_aispayloadinfo(self, bin_bytes: Any) -> AISPayloadInfo:
        """Create an AISPayloadInfo obj by way of AISPayload.get_payload_info().

        Args:
            bin_bytes: Sets the AISPayload(bin_bytes) ctor argument input.
                Accepts any input, including bad input.

        Raises:
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        ap_obj = self.create_aispayload(bin_bytes=bin_bytes)  # AISPayload object
        return ap_obj.get_payload_info()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
