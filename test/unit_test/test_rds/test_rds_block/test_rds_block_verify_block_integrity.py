"""Unit test module for RDSBlock.verify_block_integrity().

Typical Usage:
    python -m test                                           # Run *all* the test cases
    python -m test.unit_test                                 # Run *all* the unit test cases
    python -m test.unit_test.test_rds                        # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_rds_block         # Run *all* RDSBlock method test cases
    # Run just these unit tests
    python -m test.unit_test.test_rds.test_rds_block.test_rds_block_verify_block_integrity
    # Run just this normal 1 unit test
    python -m test.unit_test.test_rds.test_rds_block.test_rds_block_verify_block_integrity -k n01  
"""

# Standard Imports
from typing import Any
from unittest import skip
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
from test.test_case_data import TestCaseData
from test.unit_test.root_unit_test import RootUnitTest
# Local Imports
from gallant_input.rds.block import RDSBlock
from gallant_input.rds.block_id import BlockID
from gallant_input.rds.exceptions import RDSIntegrityFailure
from test.unit_test.test_rds.test_rds_block.test_rds_block import RDSBlockUnitTest


class RDSBlockVBIUnitTest(RDSBlockUnitTest):
    """Parent class for all RDSBlock.verify_block_integrity() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        test_obj = RDSBlock(rds_block=self.input_rds_block, block_id=self.input_block_id)
        return test_obj.verify_block_integrity(*self._args, **self._kwargs)

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

    def run_test_exception(self, rds_block: Any, block_id: Any,
                           exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            rds_block: Sets the rds_block argument input.  Accepts any input, including bad input.
            block_id: Sets the block_id argument input.  Accepts any input, including bad input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(rds_block=rds_block, block_id=block_id)
        self.set_test_input()  # This method does not take any args
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, rds_block: bytes, block_id: BlockID) -> None:
        """Common method calls for a test case expected to return.

        Args:
            rds_block: Sets the rds_block argument input.
            block_id: Sets the block_id argument input.
        """
        self.set_ctor_args(rds_block=rds_block, block_id=block_id)
        self.set_test_input()  # This method does not take any args
        self.expect_return(None)
        self.run_test()


class NormalRDSBlockVBIUnitTest(RDSBlockVBIUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_block_a(self):
        """Valid example of RDS Block A."""
        rds_block = bytes('01010111000111010101011100', 'utf-8')  # Block A example
        block_id = BlockID.BLOCK_A
        self.run_test_return(rds_block, block_id)

    def test_n02_valid_block_b(self):
        """Valid example of RDS Block B."""
        rds_block = bytes('00000001001010010010100010', 'utf-8')  # Block B example
        block_id = BlockID.BLOCK_B
        self.run_test_return(rds_block, block_id)

    # skip('Does not(?) include valid test case input yet')
    def test_n03_valid_block_c(self):
        """Valid example of RDS Block C."""
        rds_block = bytes('00001101110011011011010011', 'utf-8')  # Block C example
        block_id = BlockID.BLOCK_C
        self.run_test_return(rds_block, block_id)

    # skip('Does not(?) include valid test case input yet')
    def test_n04_valid_block_c_prime(self):
        """Valid example of RDS Block C'."""
        rds_block = bytes('00001101110011011011010011', 'utf-8')  # Block C' example
        block_id = BlockID.BLOCK_C_PRIME
        self.run_test_return(rds_block, block_id)

    def test_n05_valid_block_d(self):
        """Valid example of RDS Block D."""
        rds_block = bytes('01011100001011100100001110', 'utf-8')  # Block D example
        block_id = BlockID.BLOCK_D
        self.run_test_return(rds_block, block_id)

    def test_n06_valid_block_a_expecting_b(self):
        """Valid example of RDS Block A but it's expecting a different block."""
        rds_block = bytes('01010111000111010101011100', 'utf-8')  # Block A example
        block_id = BlockID.BLOCK_B
        exception_type = RDSIntegrityFailure
        exception_msg = ''
        self.run_test_exception(rds_block, block_id, exception_type, exception_msg)

    def test_n07_valid_block_b_expecting_c(self):
        """Valid example of RDS Block B but it's expecting a different block."""
        rds_block = bytes('00000001001010010010100010', 'utf-8')  # Block B example
        block_id = BlockID.BLOCK_C
        exception_type = RDSIntegrityFailure
        exception_msg = ''
        self.run_test_exception(rds_block, block_id, exception_type, exception_msg)

    # skip('Does not(?) include valid test case input yet')
    def test_n08_valid_block_c_expecting_c_prime(self):
        """Valid example of RDS Block C but it's expecting a different block."""
        rds_block = bytes('00001101110011011011010011', 'utf-8')  # Block C example
        block_id = BlockID.BLOCK_C_PRIME
        exception_type = RDSIntegrityFailure
        exception_msg = ''
        self.run_test_exception(rds_block, block_id, exception_type, exception_msg)

    # skip('Does not(?) include valid test case input yet')
    def test_n09_valid_block_c_prime_expecting_d(self):
        """Valid example of RDS Block C' but it's expecting a different block."""
        rds_block = bytes('00001101110011011011010011', 'utf-8')  # Block C' example
        block_id = BlockID.BLOCK_D
        exception_type = RDSIntegrityFailure
        exception_msg = ''
        self.run_test_exception(rds_block, block_id, exception_type, exception_msg)

    def test_n10_valid_block_d_expecting_a(self):
        """Valid example of RDS Block D but it's expecting a different block."""
        rds_block = bytes('01011100001011100100001110', 'utf-8')  # Block D example
        block_id = BlockID.BLOCK_A
        exception_type = RDSIntegrityFailure
        exception_msg = ''
        self.run_test_exception(rds_block, block_id, exception_type, exception_msg)


if __name__ == '__main__':
    execute_test_cases()
