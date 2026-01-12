"""Defines the root rds.mgt RDSMsgGroupType00 unit test class.

RDSMsgGrpType00UnitTest is the parent class for all rds.mgt sub-package related unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_rds.test_mgt.test_mgt import RDSMsgGrpType00UnitTest

    class RDSSomethingUnitTest(RDSMsgGrpType00UnitTest):
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
# Local Imports
from gallant_input.rds.exceptions import RDSIntegrityFailure, RDSMsgGroupTypeMissing
from gallant_input.rds.group import RDSGroup
from test.unit_test.test_rds.test_mgt.test_mgt import RDSMsgGrpTypeUnitTest


class RDSMsgGrpType00UnitTest(RDSMsgGrpTypeUnitTest):
    """Parent class for all rds.mgt RDSMsgGroupType00 specific unit tests.

    Inherit from this class, define necessary functionality for the function you're testing and
    be sure to override the following methods in your child class:
        call_callable()
        validate_return_value()

    Available features:
        See: help(TediousUnitTest)

    Attributes:
        built_rds_group:    # RDSGroup() object for this test case
        built_rds_mgt00:    # RDSMsgGroupType00() object for this test case
        test_case_data:     # Stores data about the test case as a TestCaseData object
        test_input_dir:     # Default input directory (OPTIONAL)
        test_output_dir:    # Default output directory (OPTIONAL)
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, *args, **kwargs) -> None:
        """RDSBlockUnitTest ctor."""
        # ATTRIBUTES
        self.built_rds_mgt00 = None  # RDSMsgGroupType00() object to test

        super().__init__(*args, **kwargs)

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

    def get_rds_group_msg_group00(self, rds_group: bytes, assume_na: bool = True) -> None:
        """Build an RDSMsgGroupType00() object to test."""
        self.build_rds_group(rds_group=rds_group, assume_na=assume_na)
        try:
            self.self.built_rds_mgt00 = self.built_rds_group.get_msg_group00()
        except (RDSIntegrityFailure, RDSMsgGroupTypeMissing, TypeError, ValueError) as err:
            self.fail_test_case(f'RDSGroup({rds_group}, {assume_na}).get_msg_group00() failed to '
                                'build an RDSMsgGroupType00() object as test case input: '
                                f'{repr(err)}')


    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
