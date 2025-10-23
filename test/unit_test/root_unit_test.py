"""Defines the root GAIN unit test class.

RootUnitTest is the parent class for all GAIN related unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.root_unit_test import RootUnitTest

    class GainUnitTest(RootUnitTest):
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
# Third Party Imports
from test.test_case_data import TestCaseData
from tediousstart.tediousunittest import TediousUnitTest
# Local Imports


class RootUnitTest(TediousUnitTest):
    """Parent class for all GAIN related unit tests.

    Inherit from this class, define necessary functionality for the function you're testing and
    be sure to override the following methods in your child class:
        call_callable()
        validate_return_value()

    Available features:
        See: help(TediousUnitTest)

    Attributes:
        test_case_data:     # Stores data about the test case as a TestCaseData object
        test_input_dir:     # Default input directory (OPTIONAL)
        test_output_dir:    # Default output directory (OPTIONAL)
    """

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, *args, **kwargs) -> None:
        """RootUnitTest ctor."""
        # ATTRIBUTES
        self.test_input_dir = None   # Default directory for input files
        self.test_output_dir = None  # Default directory for output files
        self.test_case_data = None   # Parse the test case names for discrete snippets

        super().__init__(*args, **kwargs)

    def setUp(self) -> None:
        """Validates test environment.

        Populates test_case_data with the test number, name, description, etc.
        """
        if self.test_input_dir is not None:
            self._validate_directory(self.test_input_dir, 'test input dir', must_exist=True)
        if self.test_output_dir is not None:
            self._validate_directory(self.test_output_dir, 'test output dir', must_exist=True)
        try:
            self.test_case_data = TestCaseData.generate_from_id(self.id())
        except (KeyError, TypeError, ValueError):
            self.test_case_data = None  # Isn't working, so don't keep it
        super().setUp()

    def tearDown(self) -> None:
        """Tear down the testing environment."""
        if self.test_output_dir is not None:
            # Empty it
            self._delete_files(dirname=self.test_output_dir, exempt=['.placeholder', '.gitkeep'])
        super().tearDown()

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

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
