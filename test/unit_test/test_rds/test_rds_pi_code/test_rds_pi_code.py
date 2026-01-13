"""Defines the root RDSPICode unit test class.

RDSPICodeUnitTest is the parent class for all rds.picode RDSPICode unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code import RDSPICodeUnitTest

    class RDSSomethingUnitTest(RDSPICodeUnitTest):
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
from test.unit_test.test_rds.test_rds import RDSUnitTest
# Local Imports
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN
from gallant_input.rds.picode import RDSPICode


class RDSPICodeUnitTest(RDSUnitTest):
    """Parent class for all RDSPICode method unit tests.

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
        input_pi_code:    # Test case input: RDSPICode(pi_code)
        input_assume_na:  # Test case input: RDSPICode(assume_na)
        test_obj:         # RDSPICode() test object created by self.create_test_obj()
    """

    # GOOD GROUP VALUES
    # GOOD SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO    "
    GOOD_SET1_GRP01_MSG00_OFF00 = \
        b'0011011001011000100001101100000000111011001101011000' \
        b'1110000110001000111110011001001011010011111111001100'  # "KO"
    GOOD_SET1_GRP02_MSG00_OFF01 = \
        b'0011011001011000100001101100000000111010010110111100' \
        b'1110000110001000111110011001001110010011110001100000'  # "NO"
    GOOD_SET1_GRP03_MSG00_OFF02 = \
        b'0011011001011000100001101100000000111010101101110111' \
        b'1110000110001000111110011000100000001000000011011100'  # "  "
    GOOD_SET1_GRP04_MSG00_OFF03 = \
        b'0011011001011000100001101100000000111011001101011000' \
        b'1110000110001000111110011001001011010011111111001100'  # "  "
    # GOOD SET 2: KONO 101.1 FM Live Capture of Group Type 02A - Radio Text ""
    GOOD_SET2_GRP01_MSG02_OFF00 = \
        b'0011011001011000100001101100100000111000000010101001' \
        b'0100101101001111110001000001001110010011110001100000'  # "KONO"
    GOOD_SET2_GRP01_MSG02_OFF01 = \
        b'0011011001011000100001101100100000111000010100010000' \
        b'0010000000110001100000011000110000001100010111010001'  # " 101"
    GOOD_SET2_GRP01_MSG02_OFF02 = \
        b'0011011001011000100001101100100000111000101111011011' \
        b'0010111000110001111001011100100000010100111101011000'  # ".1 S"
    GOOD_SET2_GRP01_MSG02_OFF03 = \
        b'0011011001011000100001101100100000111000111001100010' \
        b'0110000101101110010010000000100000010000011110010101'  # "an A"
    GOOD_SET2_GRP01_MSG02_OFF04 = \
        b'0011011001011000100001101100100000111001001111110100' \
        b'0110111001110100111010001101101111011011100001101101'  # "nton"
    GOOD_SET2_GRP01_MSG02_OFF05 = \
        b'0011011001011000100001101100100000111001011001001101' \
        b'0110100101101111111100000000100111011100111110001011'  # "io's"
    GOOD_SET2_GRP01_MSG02_OFF06 = \
        b'0011011001011000100001101100100000111001100010000110' \
        b'0010000001000111110110011001110010011001011001011011'  # " Gre"
    GOOD_SET2_GRP01_MSG02_OFF07 = \
        b'0011011001011000100001101100100000111001110100111111' \
        b'0110000101110100101110111001100101011100110011010100'  # "ates"
    GOOD_SET2_GRP01_MSG02_OFF08 = \
        b'0011011001011000100001101100100000111010001110101010' \
        b'0111010000100000101001110001001000011010010001000000'  # "t Hi"
    GOOD_SET2_GRP01_MSG02_OFF09 = \
        b'0011011001011000100001101100100000111010011000010011' \
        b'0111010001110011111101111100100000001000000011011100'  # "ts  "
    GOOD_SET2_GRP01_MSG02_OFF10 = \
        b'0011011001011000100001101100100000111010100011011000' \
        b'0010000000100000000000000000100000001000000011011100'  # "    "
    GOOD_SET2_GRP01_MSG02_OFF11 = \
        b'0011011001011000100001101100100000111010110101100001' \
        b'0010000000100000000000000000100000001000000011011100'  # "    "
    GOOD_SET2_GRP01_MSG02_OFF12 = \
        b'0011011001011000100001101100100000111011000011110111' \
        b'0010000000100000000000000000100000001000000011011100'  # "    "
    GOOD_SET2_GRP01_MSG02_OFF13 = \
        b'0011011001011000100001101100100000111011010101001110' \
        b'0010000000100000000000000000100000001000000011011100'  # "    "
    GOOD_SET2_GRP01_MSG02_OFF14 = \
        b'0011011001011000100001101100100000111011101110000101' \
        b'0010000000100000000000000000100000001000000011011100'  # "    "
    GOOD_SET2_GRP01_MSG02_OFF15 = \
        b'0011011001011000100001101100100000111011111000111100' \
        b'0010000000100000000000000000100000001000000011011100'  # "    "

    # GOOD SET VALUES
    # GOOD SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO    "
    GOOD_SET1_MSG00A = GOOD_SET1_GRP01_MSG00_OFF00 + GOOD_SET1_GRP02_MSG00_OFF01 \
        + GOOD_SET1_GRP03_MSG00_OFF02 + GOOD_SET1_GRP04_MSG00_OFF03
    # GOOD SET 2: KONO 101.1 FM Live Capture of Group Type 02A - Radio Text
    # "KONO 101.1 San Antonio's Greatest Hits                          "
    GOOD_SET2_MSG02A = \
        GOOD_SET2_GRP01_MSG02_OFF00 + GOOD_SET2_GRP01_MSG02_OFF01 \
        + GOOD_SET2_GRP01_MSG02_OFF02 + GOOD_SET2_GRP01_MSG02_OFF03 \
        + GOOD_SET2_GRP01_MSG02_OFF04 + GOOD_SET2_GRP01_MSG02_OFF05 \
        + GOOD_SET2_GRP01_MSG02_OFF06 + GOOD_SET2_GRP01_MSG02_OFF07 \
        + GOOD_SET2_GRP01_MSG02_OFF08 + GOOD_SET2_GRP01_MSG02_OFF09 \
        + GOOD_SET2_GRP01_MSG02_OFF10 + GOOD_SET2_GRP01_MSG02_OFF11 \
        + GOOD_SET2_GRP01_MSG02_OFF12 + GOOD_SET2_GRP01_MSG02_OFF13 \
        + GOOD_SET2_GRP01_MSG02_OFF14 + GOOD_SET2_GRP01_MSG02_OFF15

    # GOOD SET RESULTS
    GOOD_SET1_STATION_NAME = 'KONO    '
    GOOD_SET2_RADIO_TEXT = "KONO 101.1 San Antonio's Greatest Hits                          "

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RDSPICodeUnitTest ctor."""
        # ATTRIBUTES
        self.input_pi_code = None                                  # Test input: RDSPICode(pi_code)
        self.def_good_pic = self.GOOD_GROUP1[:RDS_BLOCK_DATA_LEN]  # A default "good" PI code
        self.test_obj = None                                       # PICode() test object

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # test_obj = RDSPICode(pi_code=self.input_pi_code, assume_na=self.input_assume_na)
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

    def create_test_obj(self, pi_code: Any) -> None:
        """Creates the PICode() test object store in self.test_obj, once."""
        if self.test_obj is None:
            self.set_ctor_args(pi_code=pi_code)
            self.test_obj = RDSPICode(pi_code=self.input_pi_code)

    def set_ctor_args(self, pi_code: Any) -> None:
        """Set the class ctor arguments.

        Args:
            pi_code: Sets the pi_code argument input.  Accepts any input,
                including bad input.
        """
        self.input_pi_code = pi_code

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
