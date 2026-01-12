"""Unit test module for RDSMsgGroupType00.station_name_chunk property.

Typical Usage:
    python -m test                                           # Run *all* the test cases
    python -m test.unit_test                                 # Run *all* the unit test cases
    python -m test.unit_test.test_rds                        # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_mgt               # Run *all* RDSMsgGroupType method test cases
    # Run just the RDSMsgGroupType00 unit tests
    python -m test.unit_test.test_rds.test_mgt.test_mgt00
    # Run just the RDSMsgGroupType00.station_name_chunk test cases
    python -m test.unit_test.test_rds.test_mgt.test_mgt00.test_mgt00_station_name_chunk
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
# Local Imports
from gallant_input.rds.constants import RDS_GROUP_LEN
from gallant_input.rds.exceptions import RDSIntegrityFailure
from gallant_input.rds.group import RDSGroup
from gallant_input.rds.group_info import RDSGroupInfo
from gallant_input.rds.rbds_program_type import RBDSProgTypeCode
from test.unit_test.test_rds.test_mgt.test_mgt00.test_mgt00 import RDSMsgGrpType00UnitTest


class RDSMsgGrpType00SNCUnitTest(RDSMsgGrpType00UnitTest):
    """Parent class for all RDSMsgGroupType00.station_name_chunk property unit tests.

    Attributes:
        built_rds_group:    # RDSGroup() object for this test case
        test_case_data:     # Stores data about the test case as a TestCaseData object
        test_input_dir:     # Default input directory (OPTIONAL)
        test_output_dir:    # Default output directory (OPTIONAL)
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the method call."""
        self.get_rds_group_msg_group00(rds_group=self.input_rds_group,
                                       assume_na=self.input_assume_na)
        return self.self.built_rds_mgt00.station_name_chunk

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)
        if isinstance(return_value, type(self._exp_return)):
            # Actual data types are checked in self._validate_return_value()
            # I want to explicitly know when there's a length mismatch
            # No need to compare the length if they're different data types
            if len(self._exp_return) != len(return_value):
                self._add_test_failure(f'Expected return value length of "{len(self._exp_return)}"'
                                       f' but received a length of "{len(return_value)}" instead')

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, rds_group: bytes, assume_na: bool,
                           exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            rds_group: Sets the rds_group argument input.  Input should be valid and well-formed.
            assume_na: Sets the assume_na argument input.  Input should be valid and well-formed.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(rds_group=rds_group, assume_na=assume_na)
        self.set_test_input()  # This method does not take any args
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, rds_group: bytes, assume_na: bool, exp_ret: str) -> None:
        """Common method calls for a test case expected to return.

        Args:
            rds_group: Sets the rds_group argument input.  Input should be valid and well-formed.
            assume_na: Sets the assume_na argument input.  Input should be valid and well-formed.
            exp_ret: Expected value of the dataclass property.
        """
        self.set_ctor_args(rds_group=rds_group, assume_na=assume_na)
        self.set_test_input()  # This dataclass property does not take any args
        self.expect_return(exp_ret)
        self.run_test()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order


class NormalRDSMsgGrpType00SNCUnitTest(RDSMsgGrpType00SNCUnitTest):
    """Normal Test Cases."""

    # TEST CASES
    # Test cases listed in numberical order

    def test_n01_good_group1_offset_0(self):
        """Live capture of a coherent RDS Group 1: Station Name Offset 0."""
        rds_group = self.GOOD_GROUP1_MSG00_OFF0
        assume_na = True
        exp_ret = '  '
        self.run_test_return(rds_group, assume_na, exp_ret)

    def test_n02_good_group2_offset_1(self):
        """Live capture of a coherent RDS Group 2: Station Name Offset 0."""
        rds_group = self.GOOD_GROUP2_MSG00_OFF0
        assume_na = True
        exp_ret = 'KO'
        self.run_test_return(rds_group, assume_na, exp_ret)

    def test_n03_good_group2_offset_1(self):
        """Live capture of a coherent RDS Group 2: Station Name Offset 1."""
        rds_group = self.GOOD_GROUP2_MSG00_OFF1
        assume_na = True
        exp_ret = 'NO'
        self.run_test_return(rds_group, assume_na, exp_ret)


if __name__ == '__main__':
    execute_test_cases()
