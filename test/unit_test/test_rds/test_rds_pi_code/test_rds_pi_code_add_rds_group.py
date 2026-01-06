"""Unit test module for RDSPICode.add_rds_group().

Typical Usage:
    python -m test                                           # Run *all* the test cases
    python -m test.unit_test                                 # Run *all* the unit test cases
    python -m test.unit_test.test_rds                        # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_rds_pi_code       # Run *all* RDSPICode method test cases
    # Run just these unit tests
    python -m test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_add_rds_group
    # Run just this normal 1 unit test
    python -m test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_add_rds_group -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN, RDS_GROUP_LEN
from gallant_input.rds.exceptions import RDSIntegrityFailure
from gallant_input.rds.group import RDSGroup
from gallant_input.rds.group_info import RDSGroupInfo
from gallant_input.rds.picode import RDSPICode
from gallant_input.rds.rbds_program_type import RBDSProgTypeCode
from test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code import RDSPICodeUnitTest


class RDSPICodeARGUnitTest(RDSPICodeUnitTest):
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
        """RDSPICodeARGUnitTest ctor."""
        # ATTRIBUTES
        self.def_good_pic = self.GOOD_GROUP1[:RDS_BLOCK_DATA_LEN]  # A default "good" PI code

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the method call."""
        test_obj = RDSPICode(pi_code=self.input_pi_code)
        return test_obj.add_rds_group(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call.

        Child class must override this method.
        See TediousUnitTest.validate_return_value() for details.
        """
        self._validate_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, pi_code: Any, rds_group: Any, exception_type: Exception,
                           exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            pi_code: Sets the pi_code argument input.  Accepts any input, including bad input.
            rds_group: The RDSGroup to pass to the method call.
                Accepts any input, including bad input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(pi_code=pi_code)
        self.set_test_input(rds_group)
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, pi_code: bytes, rds_group: RDSGroup) -> None:
        """Common method calls for a test case expected to return.

        Args:
            pi_code: Sets the pi_code ctor argument input.
            rds_group: The RDSGroup to pass to the method call.
        """
        self.set_ctor_args(pi_code=pi_code)
        self.set_test_input(rds_group)
        self.expect_return(None)  # This method does not have a return value
        self.run_test()


class NormalRDSPICodeARGUnitTest(RDSPICodeARGUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_coherent_group1(self):
        """Valid example of a coherent RDS Group."""
        pi_code = self.GOOD_GROUP1[:RDS_BLOCK_DATA_LEN]
        rds_group = RDSGroup(self.GOOD_GROUP1)
        self.run_test_return(pi_code, rds_group)


class ErrorRDSPICodeARGUnitTest(RDSPICodeARGUnitTest):
    """Error Test Cases."""

    def test_e01_rds_group_bad_obj_type_none(self):
        """Bad rds_group type: None."""
        pi_code = self.def_good_pic
        rds_group = None
        self.run_test_exception(pi_code, rds_group, TypeError, 'argument should have been of type')

    def test_e02_rds_group_bad_obj_type_tuple(self):
        """Bad rds_group type: tuple."""
        pi_code = self.def_good_pic
        rds_group = tuple((self.GOOD_BLOCK_A3, self.GOOD_BLOCK_B3, self.GOOD_BLOCK_C3,
                           self.GOOD_BLOCK_D3))
        self.run_test_exception(pi_code, rds_group, TypeError, 'argument should have been of type')

    def test_e03_rds_group_bad_obj_type_int(self):
        """Bad rds_group type: int."""
        pi_code = self.def_good_pic
        rds_group = convert_bin_bytes_to_int(self.GOOD_GROUP1)
        self.run_test_exception(pi_code, rds_group, TypeError,
                                'argument should have been of type')

    def test_e04_rds_group_bad_obj_empty_bytes(self):
        """Bad rds_group value: empty."""
        pi_code = self.def_good_pic
        rds_group = b''
        self.run_test_exception(pi_code, rds_group, TypeError,
                                'The "rds_group" argument should have been of type')

    def test_e05_rds_group_bad_type_none(self):
        """Bad rds_group type: RDSGroup(None)."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(None)
        self.run_test_exception(pi_code, rds_group, TypeError, 'argument should have been of type')

    def test_e06_rds_group_bad_type_tuple(self):
        """Bad rds_group type: RDSGroup(tuple)."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(tuple((self.GOOD_BLOCK_A3, self.GOOD_BLOCK_B3, self.GOOD_BLOCK_C3,
                           self.GOOD_BLOCK_D3)))
        self.run_test_exception(pi_code, rds_group, TypeError, 'argument should have been of type')

    def test_e07_rds_group_bad_type_int(self):
        """Bad rds_group type: RDSGroup(int)."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(convert_bin_bytes_to_int(self.GOOD_GROUP1))
        self.run_test_exception(pi_code, rds_group, TypeError,
                                'argument should have been of type')

    def test_e08_rds_group_bad_value_empty(self):
        """Bad rds_group value: RDSGroup(empty bytes)."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(b'')
        self.run_test_exception(pi_code, rds_group, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e09_rds_group_bad_value_short(self):
        """Bad rds_group value: short."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(self.GOOD_GROUP1[:RDS_GROUP_LEN-1])
        self.run_test_exception(pi_code, rds_group, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e10_rds_group_bad_value_long(self):
        """Bad rds_group value: long."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(self.GOOD_GROUP1 + b'1')
        self.run_test_exception(pi_code, rds_group, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e11_rds_group_bad_value_two_blocks(self):
        """Bad rds_group value: two groups."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(self.GOOD_GROUP1 + self.GOOD_GROUP1)
        self.run_test_exception(pi_code, rds_group, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e12_rds_group_bad_value_binary(self):
        """Bad rds_group value: binary contains an invalid character."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(self.GOOD_BLOCK_A3 + self.GOOD_BLOCK_B3 + self.GOOD_BLOCK_C3
                             + self.BAD_BLOCK8)
        self.run_test_exception(pi_code, rds_group, ValueError, 'Invalid binary value detected')


class SpecialRDSPICodeGBIUnitTest(RDSPICodeARGUnitTest):
    """Special Test Cases."""

    def test_s01_out_of_order_group_shift1(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 1."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(self.GOOD_BLOCK_D3 + self.GOOD_BLOCK_A3 + self.GOOD_BLOCK_B3 \
            + self.GOOD_BLOCK_C3)
        self.run_test_exception(pi_code, rds_group, RDSIntegrityFailure,
                                'This RDS PI code set detected a bad RDS group:')

    def test_s02_out_of_order_group_shift2(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 2."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(self.GOOD_BLOCK_C3 + self.GOOD_BLOCK_D3 + self.GOOD_BLOCK_A3 \
            + self.GOOD_BLOCK_B3)
        self.run_test_exception(pi_code, rds_group, RDSIntegrityFailure,
                                'This RDS PI code set detected a bad RDS group:')

    def test_s03_out_of_order_group_shift3(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 3."""
        pi_code = self.def_good_pic
        rds_group = RDSGroup(self.GOOD_BLOCK_B3 + self.GOOD_BLOCK_C3 + self.GOOD_BLOCK_D3 \
            + self.GOOD_BLOCK_A3)
        self.run_test_exception(pi_code, rds_group, RDSIntegrityFailure,
                                'This RDS PI code set detected a bad RDS group:')

    def test_s04_valid_yet_disparate_blocks(self):
        """A group of RDS blocks that are not necessarily related to each other."""
        pi_code = self.GOOD_BLOCK_A1[:RDS_BLOCK_DATA_LEN]
        rds_group = RDSGroup(self.GOOD_BLOCK_A1 + self.GOOD_BLOCK_B3 + self.GOOD_BLOCK_C1 \
            + self.GOOD_BLOCK_D3)
        self.run_test_return(pi_code, rds_group)


if __name__ == '__main__':
    execute_test_cases()
