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
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
from test.test_case_data import TestCaseData
from test.unit_test.root_unit_test import RootUnitTest
# Local Imports
from gallant_input.rds.block import RDSBlock
from gallant_input.rds.block_id import BlockID
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
        return test_obj.verify_block_integrity()  # This method does not take any args

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

    def run_test_success(self, rds_block: bytes, block_id: BlockID) -> None:
        """Common method calls for a test case expected to succeed."""
        self.set_ctor_args(rds_block=rds_block, block_id=block_id)
        self.set_test_input(None)  # This method does not take any args
        self.expect_return(None)
        self.run_test()


class NormalRDSBlockVBIUnitTest(RDSBlockVBIUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_block_a(self):
        """Valid example of RDS Block A."""
        rds_block = bytes('01010111000111010101011100', 'utf-8')  # Block A example
        block_id = BlockID.BLOCK_A
        self.run_test_success(rds_block, block_id)


if __name__ == '__main__':
    execute_test_cases()
