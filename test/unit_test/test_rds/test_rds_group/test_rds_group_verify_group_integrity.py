"""Unit test module for RDSGroup.verify_group_integrity().

Typical Usage:
    python -m test                                           # Run *all* the test cases
    python -m test.unit_test                                 # Run *all* the unit test cases
    python -m test.unit_test.test_rds                        # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_rds_group         # Run *all* RDSGroup method test cases
    # Run just these unit tests
    python -m test.unit_test.test_rds.test_rds_group.test_rds_group_verify_group_integrity
    # Run just this normal 1 unit test
    python -m test.unit_test.test_rds.test_rds_group.test_rds_group_verify_group_integrity -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
# Local Imports
from gallant_input.rds.constants import RDS_GROUP_LEN
from gallant_input.rds.group import RDSGroup
from gallant_input.rds.exceptions import RDSIntegrityFailure
from test.unit_test.test_rds.test_rds_group.test_rds_group import RDSGroupUnitTest


class RDSGroupVGIUnitTest(RDSGroupUnitTest):
    """Parent class for all RDSGroup.verify_group_integrity() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the method call."""
        test_obj = RDSGroup(rds_group=self.input_rds_group, assume_na=self.input_assume_na)
        return test_obj.verify_group_integrity(*self._args, **self._kwargs)

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

    def run_test_exception(self, rds_group: Any, assume_na: Any,
                           exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            rds_group: Sets the rds_group argument input.  Accepts any input, including bad input.
            assume_na: Sets the assume_na argument input.  Accepts any input, including bad input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(rds_group=rds_group, assume_na=assume_na)
        self.set_test_input()  # This method does not take any args
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, rds_group: bytes, assume_na: bool) -> None:
        """Common method calls for a test case expected to return.

        Args:
            rds_group: Sets the rds_group argument input.
            assume_na: Sets the assume_na argument input.
        """
        self.set_ctor_args(rds_group=rds_group, assume_na=assume_na)
        self.set_test_input()  # This method does not take any args
        self.expect_return(None)
        self.run_test()


class NormalRDSGroupVGIUnitTest(RDSGroupVGIUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_coherent_group1(self):
        """Valid example of a coherent RDS Group."""
        rds_group = self.good_group1
        assume_na = True
        self.run_test_return(rds_group, assume_na)

    def test_n02_valid_coherent_group1_different_continent(self):
        """Valid example of a coherent RDS Group but assume it's not from North America."""
        rds_group = self.good_group1
        assume_na = False
        self.run_test_return(rds_group, assume_na)


class ErrorRDSGroupVGIUnitTest(RDSGroupVGIUnitTest):
    """Error Test Cases."""

    def test_e01_rds_group_bad_type_none(self):
        """Bad rds_group type: None."""
        rds_group = self.BAD_BLOCK1
        assume_na = True
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e02_rds_group_bad_type_tuple(self):
        """Bad rds_group type: tuple."""
        rds_group = tuple((self.good_block_a3, self.good_block_b3,
                           self.good_block_c3, self.good_block_d3))
        assume_na = True
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e03_rds_group_bad_type_int(self):
        """Bad rds_group type: int."""
        rds_group = self.BAD_BLOCK3*4
        assume_na = True
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e04_rds_group_bad_value_empty(self):
        """Bad rds_group value: empty."""
        rds_group = self.BAD_BLOCK4
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e05_rds_group_bad_value_short(self):
        """Bad rds_group value: short."""
        rds_group = self.good_group1[:RDS_GROUP_LEN-1]
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e06_rds_group_bad_value_long(self):
        """Bad rds_group value: long."""
        rds_group = self.good_group1 + b'0'
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e07_rds_group_bad_value_two_blocks(self):
        """Bad rds_group value: two groups."""
        rds_group = self.good_group1 + self.good_group1
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e08_rds_group_bad_value_binary(self):
        """Bad rds_group value: binary contains an invalid character."""
        rds_group = self.good_block_a3 + self.good_block_b3 + self.good_block_c3 + self.BAD_BLOCK8
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'Invalid binary value detected')

    def test_e09_assume_na_bad_type_none(self):
        """Bad assume_na type: None."""
        rds_group = self.good_group1
        assume_na = None
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e10_assume_na_bad_type_tuple(self):
        """Bad assume_na type: tuple."""
        rds_group = self.good_group1
        assume_na = tuple((self.good_group1, True))
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e11_assume_na_bad_type_int(self):
        """Bad assume_na type: int."""
        rds_group = self.good_group1
        assume_na = 1  # True value
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')


class SpecialRDSGroupGBIUnitTest(RDSGroupVGIUnitTest):
    """Special Test Cases."""

    def test_s01_out_of_order_group_shift1(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 1."""
        rds_group = self.good_block_d3 + self.good_block_a3 + self.good_block_b3 \
            + self.good_block_c3
        assume_na = True
        self.run_test_exception(rds_group, assume_na, RDSIntegrityFailure,
                                'This RDS group failed its integrity check:')

    def test_s02_out_of_order_group_shift2(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 2."""
        rds_group = self.good_block_c3 + self.good_block_d3 + self.good_block_a3 \
            + self.good_block_b3
        assume_na = True
        self.run_test_exception(rds_group, assume_na, RDSIntegrityFailure,
                                'This RDS group failed its integrity check:')

    def test_s03_out_of_order_group_shift3(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 3."""
        rds_group = self.good_block_b3 + self.good_block_c3 + self.good_block_d3 \
            + self.good_block_a3
        assume_na = True
        self.run_test_exception(rds_group, assume_na, RDSIntegrityFailure,
                                'This RDS group failed its integrity check:')

    def test_s04_valid_yet_disparate_blocks(self):
        """A group of RDS blocks that are not necessarily related to each other."""
        rds_group = self.good_block_a1 + self.good_block_b3 + self.good_block_c1 \
            + self.good_block_d3
        assume_na = True
        self.run_test_return(rds_group, assume_na)


if __name__ == '__main__':
    execute_test_cases()
