"""Unit test module for RDSBlock.get_block_id().

Typical Usage:
    python -m test                                           # Run *all* the test cases
    python -m test.unit_test                                 # Run *all* the unit test cases
    python -m test.unit_test.test_rds                        # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_rds_block         # Run *all* RDSBlock method test cases
    # Run just these unit tests
    python -m test.unit_test.test_rds.test_rds_block.test_rds_block_get_block_id
    # Run just this normal 1 unit test
    python -m test.unit_test.test_rds.test_rds_block.test_rds_block_get_block_id -k n01
"""

# Standard Imports
from typing import Any
from unittest import skip
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
# Local Imports
from gallant_input.rds.block import RDSBlock
from gallant_input.rds.block_id import BlockID
from gallant_input.rds.exceptions import RDSIntegrityFailure
from test.unit_test.test_rds.test_rds_block.test_rds_block import RDSBlockUnitTest


class RDSBlockGBIUnitTest(RDSBlockUnitTest):
    """Parent class for all RDSBlock.get_block_id() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        test_obj = RDSBlock(rds_block=self.input_rds_block, block_id=self.input_block_id)
        return test_obj.get_block_id(*self._args, **self._kwargs)

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

    def run_test_exception(self, rds_block: Any, in_block_id: Any,
                           exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            rds_block: Sets the rds_block argument input.  Accepts any input, including bad input.
            in_block_id: Sets the block_id argument input.  Accepts any input, including bad input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(rds_block=rds_block, block_id=in_block_id)
        self.set_test_input()  # This method does not take any args
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_exception_mismatch(self, rds_block: bytes, in_block_id: BlockID) -> None:
        """Common method call for a test case expected to raise a RDSIntegrityFailure exception.

        Args:
            rds_block: Sets the rds_block argument input.  Accepts any input, including bad input.
            in_block_id: Sets the block_id argument input.  Accepts any input, including bad input.
        """
        exc_msg = 'This RDS block failed its integrity check: ' + \
                  f'This block is not a {in_block_id.name} block'
        self.run_test_exception(rds_block=rds_block, in_block_id=in_block_id,
                                exception_type=RDSIntegrityFailure, exception_msg=exc_msg)

    def run_test_return(self, rds_block: bytes, in_block_id: BlockID,
                        out_block_id: BlockID) -> None:
        """Common method calls for a test case expected to return.

        Args:
            rds_block: Sets the rds_block argument input.
            in_block_id: Sets the block_id argument input.
            out_block_id: Expected return value.
        """
        self.set_ctor_args(rds_block=rds_block, block_id=in_block_id)
        self.set_test_input()  # This method does not take any args
        self.expect_return(out_block_id)
        self.run_test()


class NormalRDSBlockGBIUnitTest(RDSBlockGBIUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_block_a(self):
        """Valid example of RDS Block A."""
        rds_block = self.GOOD_BLOCK_A1  # Block A example
        block_id = BlockID.BLOCK_A
        self.run_test_return(rds_block, block_id, block_id)

    def test_n02_valid_block_b(self):
        """Valid example of RDS Block B."""
        rds_block = self.GOOD_BLOCK_B1  # Block B example
        block_id = BlockID.BLOCK_B
        self.run_test_return(rds_block, block_id, block_id)

    def test_n03_valid_block_c(self):
        """Valid example of RDS Block C."""
        rds_block = self.GOOD_BLOCK_C1  # Block C example
        block_id = BlockID.BLOCK_C
        self.run_test_return(rds_block, block_id, block_id)

    @skip('Does not include valid test case input yet')
    def test_n04_valid_block_c_prime(self):
        """Valid example of RDS Block C'."""
        rds_block = self.GOOD_BLOCK_C_PRIME1  # Block C' example
        block_id = BlockID.BLOCK_C_PRIME
        self.run_test_return(rds_block, block_id, block_id)

    def test_n05_valid_block_d(self):
        """Valid example of RDS Block D."""
        rds_block = self.GOOD_BLOCK_D1  # Block D example
        block_id = BlockID.BLOCK_D
        self.run_test_return(rds_block, block_id, block_id)

    def test_n06_valid_block_a_expecting_b(self):
        """Valid example of RDS Block A but it's expecting a different block."""
        rds_block = self.GOOD_BLOCK_A1  # Block A example
        block_id = BlockID.BLOCK_B
        self.run_test_exception_mismatch(rds_block, block_id)

    def test_n07_valid_block_b_expecting_c(self):
        """Valid example of RDS Block B but it's expecting a different block."""
        rds_block = self.GOOD_BLOCK_B1  # Block B example
        block_id = BlockID.BLOCK_C
        self.run_test_exception_mismatch(rds_block, block_id)

    def test_n08_valid_block_c_expecting_c_prime(self):
        """Valid example of RDS Block C but it's expecting a different block."""
        rds_block = self.GOOD_BLOCK_C1  # Block C example
        block_id = BlockID.BLOCK_C_PRIME
        self.run_test_exception_mismatch(rds_block, block_id)

    @skip('Does not include valid test case input yet')
    def test_n09_valid_block_c_prime_expecting_d(self):
        """Valid example of RDS Block C' but it's expecting a different block."""
        rds_block = self.GOOD_BLOCK_C_PRIME1  # Block C' example
        block_id = BlockID.BLOCK_D
        self.run_test_exception_mismatch(rds_block, block_id)

    def test_n10_valid_block_d_expecting_a(self):
        """Valid example of RDS Block D but it's expecting a different block."""
        rds_block = self.GOOD_BLOCK_D1  # Block D example
        block_id = BlockID.BLOCK_A
        self.run_test_exception_mismatch(rds_block, block_id)


class ErrorRDSBlockGBIUnitTest(RDSBlockGBIUnitTest):
    """Error Test Cases."""

    def test_e01_rds_block_bad_type_none(self):
        """Bad rds_block type: None."""
        rds_block = self.BAD_BLOCK1
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, TypeError, 'argument should have been of type')

    def test_e02_rds_block_bad_type_tuple(self):
        """Bad rds_block type: tuple."""
        rds_block = self.BAD_BLOCK2
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, TypeError, 'argument should have been of type')

    def test_e03_rds_block_bad_type_int(self):
        """Bad rds_block type: int."""
        rds_block = self.BAD_BLOCK3
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, TypeError, 'argument should have been of type')

    def test_e04_rds_block_bad_value_empty(self):
        """Bad rds_block value: empty."""
        rds_block = self.BAD_BLOCK4
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, ValueError, 'The "rds_block" argument must be of length "26" instead of')

    def test_e05_rds_block_bad_value_short(self):
        """Bad rds_block value: short."""
        rds_block = self.BAD_BLOCK5
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, ValueError, 'The "rds_block" argument must be of length "26" instead of')

    def test_e06_rds_block_bad_value_long(self):
        """Bad rds_block value: long."""
        rds_block = self.BAD_BLOCK6
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, ValueError, 'The "rds_block" argument must be of length "26" instead of')

    def test_e07_rds_block_bad_value_two_blocks(self):
        """Bad rds_block value: two blocks."""
        rds_block = self.BAD_BLOCK7
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, ValueError, 'The "rds_block" argument must be of length "26" instead of')

    def test_e08_rds_block_bad_value_binary(self):
        """Bad rds_block value: binary contains an invalid character."""
        rds_block = self.BAD_BLOCK8
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, ValueError, 'Invalid binary value detected')

    def test_e09_block_id_bad_type_none(self):
        """Bad block_id type: None."""
        rds_block = self.GOOD_BLOCK_A1
        block_id = None
        self.run_test_exception(rds_block, block_id, TypeError, 'argument should have been of type')

    def test_e10_block_id_bad_type_tuple(self):
        """Bad block_id type: tuple."""
        rds_block = self.GOOD_BLOCK_A1
        block_id = tuple((self.GOOD_BLOCK_A1, BlockID.GUESS))
        self.run_test_exception(rds_block, block_id, TypeError, 'argument should have been of type')

    def test_e11_block_id_bad_type_int(self):
        """Bad block_id type: int."""
        rds_block = self.GOOD_BLOCK_A1
        block_id = 9  # BlockID.GUESS value
        self.run_test_exception(rds_block, block_id, TypeError, 'argument should have been of type')

    def test_e12_block_id_bad_value_empty(self):
        """Bad block_id value: undetermined."""
        rds_block = self.GOOD_BLOCK_A1
        block_id = BlockID.UNKNOWN
        self.run_test_exception(rds_block, block_id, RDSIntegrityFailure,
                                'This RDS block failed its integrity check: '
                                'Will not match an UNKNOWN Block ID')


class SpecialRDSBlockGBIUnitTest(RDSBlockGBIUnitTest):
    """Special Test Cases."""

    def test_s01_valid_block_a(self):
        """Guess a valid RDS Block A."""
        rds_block = self.GOOD_BLOCK_A1  # Block A example
        in_block_id = BlockID.GUESS
        out_block_id = BlockID.BLOCK_A
        self.run_test_return(rds_block, in_block_id, out_block_id)

    def test_s02_valid_block_b(self):
        """Guess a valid RDS Block B."""
        rds_block = self.GOOD_BLOCK_B1  # Block B example
        in_block_id = BlockID.GUESS
        out_block_id = BlockID.BLOCK_B
        self.run_test_return(rds_block, in_block_id, out_block_id)

    def test_s03_valid_block_c(self):
        """Guess a valid RDS Block C."""
        rds_block = self.GOOD_BLOCK_C1  # Block C example
        in_block_id = BlockID.GUESS
        out_block_id = BlockID.BLOCK_C
        self.run_test_return(rds_block, in_block_id, out_block_id)

    @skip('Does not include valid test case input yet')
    def test_s04_valid_block_c_prime(self):
        """Guess a valid RDS Block C'."""
        rds_block = self.GOOD_BLOCK_C_PRIME1  # Block C' example
        in_block_id = BlockID.GUESS
        out_block_id = BlockID.BLOCK_C_PRIME
        self.run_test_return(rds_block, in_block_id, out_block_id)

    def test_s05_valid_block_d(self):
        """Guess a valid RDS Block D."""
        rds_block = self.GOOD_BLOCK_D1  # Block D example
        in_block_id = BlockID.GUESS
        out_block_id = BlockID.BLOCK_D
        self.run_test_return(rds_block, in_block_id, out_block_id)

    def test_s06_valid_block_c(self):
        """Guess a valid RDS Block C between C or C'."""
        rds_block = self.GOOD_BLOCK_C1  # Block C example
        in_block_id = BlockID.BLOCK_C_OR_CP
        out_block_id = BlockID.BLOCK_C
        self.run_test_return(rds_block, in_block_id, out_block_id)

    @skip('Does not include valid test case input yet')
    def test_s07_valid_block_c_prime(self):
        """Guess a valid RDS Block C' between C or C'."""
        rds_block = self.GOOD_BLOCK_C_PRIME1  # Block C' example
        in_block_id = BlockID.BLOCK_C_OR_CP
        out_block_id = BlockID.BLOCK_C_PRIME
        self.run_test_return(rds_block, in_block_id, out_block_id)

    @skip('Does not include valid test case input yet')
    def test_s08_block_e_support1(self):
        """Block E is not yet supported: sample 1."""
        rds_block = self.GOOD_BLOCK_E1
        block_id = BlockID.BLOCK_E
        self.run_test_exception(rds_block, block_id, NotImplementedError, 'No support for Block E')

    def test_s09_block_e_support2(self):
        """Block E is not yet supported: sample 2."""
        rds_block = self.GOOD_BLOCK_E2
        block_id = BlockID.BLOCK_E
        self.run_test_exception(rds_block, block_id, NotImplementedError, 'No support for Block E')

    @skip('Does not include valid test case input yet')
    def test_s10_block_e_guess1(self):
        """Guess Block E is not yet supported: sample 1."""
        rds_block = self.GOOD_BLOCK_E1
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, RDSIntegrityFailure,
                                'This RDS block failed its integrity check: '
                                'Unable to match a valid Block ID')

    def test_s11_block_e_guess2(self):
        """Guess Block E is not yet supported: sample 2."""
        rds_block = self.GOOD_BLOCK_E2
        block_id = BlockID.GUESS
        self.run_test_exception(rds_block, block_id, RDSIntegrityFailure,
                                'This RDS block failed its integrity check: '
                                'Unable to match a valid Block ID')

    def test_s12_guess_block_c1_fail(self):
        """Guess Block C*: Block A."""
        rds_block = self.GOOD_BLOCK_A1
        block_id = BlockID.BLOCK_C_OR_CP
        self.run_test_exception(rds_block, block_id, RDSIntegrityFailure,
                                'This RDS block failed its integrity check: '
                                "Unable to match a valid C or C' Block ID")

    def test_s13_valid_block_unknown_fail(self):
        """Unknown input: Block A."""
        rds_block = self.GOOD_BLOCK_A1
        block_id = BlockID.UNKNOWN
        self.run_test_exception(rds_block, block_id, RDSIntegrityFailure,
                                'This RDS block failed its integrity check: '
                                'Will not match an UNKNOWN Block ID')


if __name__ == '__main__':
    execute_test_cases()
