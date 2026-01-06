"""Defines the root RDSBlock unit test class.

RDSBlockUnitTest is the parent class for all rds.block RDSBlock unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_rds.test_rds_block.test_rds_block import RDSBlockUnitTest

    class RDSSomethingUnitTest(RDSBlockUnitTest):
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


class RDSBlockUnitTest(RDSUnitTest):
    """Parent class for all RDSBlock method unit tests.

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
        input_rds_block:  # Test case input: RDSBlock(rds_block)
        input_block_id:   # Test case input: RDSBlock(block_id)
    """

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, *args, **kwargs) -> None:
        """RDSBlockUnitTest ctor."""
        # ATTRIBUTES
        self.input_rds_block = None  # Test case input: RDSBlock(rds_block)
        self.input_block_id = None   # Test case input: RDSBlock(block_id)

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # test_obj = RDSBlock(rds_block=self.input_rds_block, block_id=self.input_block_id)
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

    def set_ctor_args(self, rds_block: Any, block_id: Any) -> None:
        """Set the class ctor arguments.

        Args:
            rds_block: Sets the rds_block argument input.  Accepts any input, including bad input.
            block_id: Sets the block_id argument input.  Accepts any input, including bad input.
        """
        self.input_rds_block = rds_block
        self.input_block_id = block_id

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
