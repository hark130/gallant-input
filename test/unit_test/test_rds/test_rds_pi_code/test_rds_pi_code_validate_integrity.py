"""Unit test module for RDSPICode.add_rds_group().

Typical Usage:
    python -m test                                      # Run *all* the test cases
    python -m test.unit_test                            # Run *all* the unit test cases
    python -m test.unit_test.test_rds                   # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_rds_pi_code  # Run *all* RDSPICode method test cases
    # Run just these unit tests
    python -m test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_validate_integrity
    # Run just this normal 1 unit test
    python -m test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_validate_integrity -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN
from gallant_input.rds.picode import RDSPICode
from test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code import RDSPICodeUnitTest


class RDSPICodeVPCIUnitTest(RDSPICodeUnitTest):
    """Parent class for all RDSPICode.add_rds_group() unit tests.

    Attributes:
        test_case_data:   # Stores data about the test case as a TestCaseData object
        test_input_dir:   # Default input directory (OPTIONAL)
        test_output_dir:  # Default output directory (OPTIONAL)
        input_pi_code:  # Test case input: RDSPICode(pi_code)
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RDSPICodeVPCIUnitTest ctor."""
        # ATTRIBUTES
        self.exp_attr_dict = None  # Dictionary of RDSPICodeInfo attrs : values to validate

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the method call."""
        test_obj = RDSPICode(pi_code=self.input_pi_code)
        return test_obj.verify_pi_code_integrity(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, pi_code: Any, exception_type: Exception,
                           exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            pi_code: Sets the pi_code argument input.  Accepts any input, including bad input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(pi_code=pi_code)
        self.set_test_input()  # This method does not take any arguments
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, pi_code: bytes) -> None:
        """Common method calls for a test case expected to return.

        Args:
            pi_code: Sets the pi_code ctor argument input.
        """
        self.set_ctor_args(pi_code=pi_code)
        self.set_test_input()  # This method does not take any arguments
        self.expect_return(None)  # This method does not have a return value
        self.run_test()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order


class NormalRDSPICodeVPCIUnitTest(RDSPICodeVPCIUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_coherent_group1(self):
        """Valid example of a coherent RDS Group."""
        pi_code = self.def_good_pic
        self.run_test_return(pi_code)


class ErrorRDSPICodeVPCIUnitTest(RDSPICodeVPCIUnitTest):
    """Error Test Cases."""

    def test_e01_pi_code_bad_type_none(self):
        """Bad pi_code type: None."""
        pi_code = None
        self.run_test_exception(pi_code, TypeError, 'argument should have been of type')

    def test_e02_pi_code_bad_type_tuple(self):
        """Bad pi_code type: tuple."""
        pi_code = tuple((self.def_good_pic))
        self.run_test_exception(pi_code, TypeError, 'argument should have been of type')

    def test_e03_pi_code_bad_type_int(self):
        """Bad pi_code type: int."""
        pi_code = convert_bin_bytes_to_int(self.def_good_pic)
        self.run_test_exception(pi_code, TypeError, 'argument should have been of type')

    def test_e04_pi_code_bad_value_empty(self):
        """Bad pi_code value: empty."""
        pi_code = b''
        self.run_test_exception(pi_code, ValueError, 'The "pi_code" argument must '
                                'be of length "16" instead of')

    def test_e05_pi_code_bad_value_short(self):
        """Bad pi_code value: short."""
        pi_code = self.def_good_pic[:RDS_BLOCK_DATA_LEN-1]
        self.run_test_exception(pi_code, ValueError, 'The "pi_code" argument must '
                                'be of length "16" instead of')

    def test_e06_pi_code_bad_value_long(self):
        """Bad pi_code value: long."""
        pi_code = self.def_good_pic + b'0'
        self.run_test_exception(pi_code, ValueError, 'The "pi_code" argument must '
                                'be of length "16" instead of')

    def test_e07_pi_code_bad_value_two_blocks(self):
        """Bad pi_code value: full RDS block."""
        pi_code = self.GOOD_BLOCK_A1
        self.run_test_exception(pi_code, ValueError, 'The "pi_code" argument must '
                                'be of length "16" instead of')

    def test_e08_pi_code_bad_value_binary(self):
        """Bad pi_code value: binary contains an invalid character."""
        pi_code = self.BAD_BLOCK8[:RDS_BLOCK_DATA_LEN]
        self.run_test_exception(pi_code, ValueError, 'Invalid binary value detected')


class SpecialRDSPICodeVPCIIUnitTest(RDSPICodeVPCIUnitTest):
    """Special Test Cases."""

    def test_s01_out_of_order_group_shift1(self):
        """Block D (instead of A): caesar shift 1.

        This test case looks like it should fail but will actually succeed because (I don't believe)
        that PI codes have a discernable format.  However, subsequent attempts to add this block
        as a Block A should fail (e.g., add_bytes(), add_rds_group())
        """
        pi_code = self.GOOD_BLOCK_D3[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code)

    def test_s02_out_of_order_group_shift2(self):
        """Block C (instead of A): caesar shift 2.

        This test case looks like it should fail but will actually succeed because (I don't believe)
        that PI codes have a discernable format.  However, subsequent attempts to add this block
        as a Block A should fail (e.g., add_bytes(), add_rds_group())
        """
        pi_code = self.GOOD_BLOCK_C3[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code)

    def test_s03_out_of_order_group_shift3(self):
        """Block B (instead of A): caesar shift 3.

        This test case looks like it should fail but will actually succeed because (I don't believe)
        that PI codes have a discernable format.  However, subsequent attempts to add this block
        as a Block A should fail (e.g., add_bytes(), add_rds_group())
        """
        pi_code = self.GOOD_BLOCK_B3[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code)


if __name__ == '__main__':
    execute_test_cases()
