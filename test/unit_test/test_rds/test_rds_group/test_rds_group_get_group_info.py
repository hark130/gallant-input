"""Unit test module for RDSGroup.get_group_info().

Typical Usage:
    python -m test                                           # Run *all* the test cases
    python -m test.unit_test                                 # Run *all* the unit test cases
    python -m test.unit_test.test_rds                        # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_rds_group         # Run *all* RDSGroup method test cases
    # Run just these unit tests
    python -m test.unit_test.test_rds.test_rds_group.test_rds_group_get_group_info
    # Run just this normal 1 unit test
    python -m test.unit_test.test_rds.test_rds_group.test_rds_group_get_group_info -k n01
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
from test.unit_test.test_rds.test_rds_group.test_rds_group import RDSGroupUnitTest


class RDSGroupGGIUnitTest(RDSGroupUnitTest):
    """Parent class for all RDSGroup.get_group_info() unit tests.

    Attributes:
        test_case_data:   # Stores data about the test case as a TestCaseData object
        test_input_dir:   # Default input directory (OPTIONAL)
        test_output_dir:  # Default output directory (OPTIONAL)
        input_rds_group:  # Test case input: RDSGroup(rds_group)
        input_assume_na:  # Test case input: RDSGroup(assume_na)
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RootUnitTest ctor."""
        # ATTRIBUTES
        self.exp_attr_dict = None  # Dictionary of RDSGroupInfo attrs : values to validate

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the method call."""
        test_obj = RDSGroup(rds_group=self.input_rds_group, assume_na=self.input_assume_na)
        return test_obj.get_group_info(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call.

        Child class must override this method.
        See TediousUnitTest.validate_return_value() for details.
        """
        # LOCAL VARIABLES
        exp_type = RDSGroupInfo  # Expected type of the return value

        # VALIDATE IT
        # Type
        if not isinstance(return_value, exp_type):
            self._add_test_failure(f'Expected type {exp_type} '
                                   f'but it was of type {type(return_value)}')
            self._add_test_failure('The contents of the return value were not investigated')
        # Value
        # NOTE: RDSGroupInfo() will be extended as features are added.  As such, we will just
        # compare the attributes that were provided by the test author against the data class
        # that was returned.
        else:
            self._validate_group_info(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _validate_group_info(self, return_value: RDSGroupInfo) -> None:
        """Validate the RDSGroupInfo returned by a method call against test author expected values.

        Validate the contents of the RDSGroupInfo returned by the method call against test
        author-defined dictionaries of attributes and/or methods (as properties) and their expected
        values in the return_value data class.

        Args:
            return_value: The RDSGroupInfo data class returned by the method call.
        """
        # VALIDATE IT
        # Ask it to validate itself
        try:
            return_value.validate_data()
        except (TypeError, ValueError) as err:
            self._add_test_failure('The returned RDSGroupInfo dataclass failed its own '
                                   f'validation: {err}')
        # Attrs
        self._validate_group_info_attrs(return_value=return_value)

    def _validate_group_info_attrs(self, return_value: RDSGroupInfo) -> None:
        """Validate the RDSGroupInfo returned by the method call against test author expected attrs.

        Validate the contents of the RDSGroupInfo returned by the method call against a test
        author-defined dictionary of attribute names (key) and their expected values (val) in the
        return_value data class.

        Args:
            return_value: The RDSGroupInfo data class returned by the method call.
        """
        # LOCAL VARIABLES
        temp_attr_val = None  # Temporary variable holding one value from return_value
        temp_exp_type = None  # Temporary variable holding the expected value data type

        # VALIDATE IT
        # Ask it to validate itself
        try:
            return_value.validate_data()
        except (TypeError, ValueError) as err:
            self._add_test_failure('The returned RDSGroupInfo dataclass failed its own '
                                   f'validation: {err}')
        # Validate the test author's exp_attr : exp_val dictionary
        if isinstance(self.exp_attr_dict, dict):
            for exp_attr, exp_val in self.exp_attr_dict.items():
                # Present?
                try:
                    temp_attr_val = getattr(return_value, exp_attr)
                except AttributeError:
                    self._add_test_failure('The RDSGroupInfo return value does not contain '
                                           f'attribute "{exp_attr}"')
                else:
                    temp_exp_type = type(exp_val)
                    # Type
                    if not isinstance(temp_attr_val, temp_exp_type):
                        self._add_test_failure(f'Expected type "{temp_exp_type}" for RDSGroupInfo '
                                               f'attr "{exp_attr}" but it was of type '
                                               f'"{type(temp_attr_val)}" instead')
                    # Value
                    elif temp_attr_val != exp_val:
                        self._add_test_failure(f'Expected value "{exp_val}" for RDSGroupInfo attr '
                                               f'"{exp_attr}" but received '
                                               f'"{temp_attr_val}" instead')

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

    def run_test_return(self, rds_group: bytes, assume_na: bool, exp_attr: dict = None) -> None:
        """Common method calls for a test case expected to return.

        Args:
            rds_group: Sets the rds_group argument input.
            assume_na: Sets the assume_na argument input.
            exp_attr: [OPTIONAL] A dictionary of RDSGroupInfo attributes, and their expected values,
                to test in the actual return value.
        """
        self.set_ctor_args(rds_group=rds_group, assume_na=assume_na)
        self.set_test_input()  # This method does not take any args
        self.expect_return(None)  # This method has a return value but validation will be customized
        self.exp_attr_dict = exp_attr
        self.run_test()


class NormalRDSGroupGGIUnitTest(RDSGroupGGIUnitTest):
    """Normal Test Cases."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RootUnitTest ctor."""
        # ATTRIBUTES
        # Dictionary of expected RDSGroupInfo attr-to-validate : expected-value
        self.good_group1_exp_info = {
            # Attributes
            'pic': bytes('0101011100011101', 'utf-8'), 'gtype': bytes('0010', 'utf-8'),
            'msg_ver': bytes('0', 'utf-8'), 'tp': bytes('0', 'utf-8'),
            'pty': bytes('01001', 'utf-8'),
            # Properties
            'group_type': 2, 'msg_group_type_a': True, 'msg_group_type_b': False,
            'traffic_reports': False,
            # This "property" expected value assumes "assume_na" is True
            'program_type': RBDSProgTypeCode(9),
        }

        super().__init__(*args, **kwargs)

    # TEST CASES
    # Test cases listed in numberical order

    def test_n01_valid_coherent_group1(self):
        """Valid example of a coherent RDS Group."""
        rds_group = self.GOOD_GROUP1
        assume_na = True
        exp_attr = self.good_group1_exp_info
        self.run_test_return(rds_group, assume_na, exp_attr)


class ErrorRDSGroupGGIUnitTest(RDSGroupGGIUnitTest):
    """Error Test Cases."""

    def test_e01_rds_group_bad_type_none(self):
        """Bad rds_group type: None."""
        rds_group = self.BAD_BLOCK1
        assume_na = True
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e02_rds_group_bad_type_tuple(self):
        """Bad rds_group type: tuple."""
        rds_group = tuple((self.GOOD_BLOCK_A3, self.GOOD_BLOCK_B3,
                           self.GOOD_BLOCK_C3, self.GOOD_BLOCK_D3))
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
        rds_group = self.GOOD_GROUP1[:RDS_GROUP_LEN-1]
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e06_rds_group_bad_value_long(self):
        """Bad rds_group value: long."""
        rds_group = self.GOOD_GROUP1 + b'0'
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e07_rds_group_bad_value_two_blocks(self):
        """Bad rds_group value: two groups."""
        rds_group = self.GOOD_GROUP1 + self.GOOD_GROUP1
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'The "rds_group" argument must '
                                'be of length "104" instead of')

    def test_e08_rds_group_bad_value_binary(self):
        """Bad rds_group value: binary contains an invalid character."""
        rds_group = self.GOOD_BLOCK_A3 + self.GOOD_BLOCK_B3 + self.GOOD_BLOCK_C3 + self.BAD_BLOCK8
        assume_na = True
        self.run_test_exception(rds_group, assume_na, ValueError, 'Invalid binary value detected')

    def test_e09_assume_na_bad_type_none(self):
        """Bad assume_na type: None."""
        rds_group = self.GOOD_GROUP1
        assume_na = None
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e10_assume_na_bad_type_tuple(self):
        """Bad assume_na type: tuple."""
        rds_group = self.GOOD_GROUP1
        assume_na = tuple((self.GOOD_GROUP1, True))
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')

    def test_e11_assume_na_bad_type_int(self):
        """Bad assume_na type: int."""
        rds_group = self.GOOD_GROUP1
        assume_na = 1  # True value
        self.run_test_exception(rds_group, assume_na, TypeError,
                                'argument should have been of type')


class SpecialRDSGroupGBIUnitTest(RDSGroupGGIUnitTest):
    """Special Test Cases."""

    def test_s01_out_of_order_group_shift1(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 1."""
        rds_group = self.GOOD_BLOCK_D3 + self.GOOD_BLOCK_A3 + self.GOOD_BLOCK_B3 \
            + self.GOOD_BLOCK_C3
        assume_na = True
        self.run_test_exception(rds_group, assume_na, RDSIntegrityFailure,
                                'This RDS group failed its integrity check:')

    def test_s02_out_of_order_group_shift2(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 1."""
        rds_group = self.GOOD_BLOCK_C3 + self.GOOD_BLOCK_D3 + self.GOOD_BLOCK_A3 \
            + self.GOOD_BLOCK_B3
        assume_na = True
        self.run_test_exception(rds_group, assume_na, RDSIntegrityFailure,
                                'This RDS group failed its integrity check:')

    def test_s03_out_of_order_group_shift3(self):
        """A group of RDS blocks that are valid but out of order: caesar shift 1."""
        rds_group = self.GOOD_BLOCK_B3 + self.GOOD_BLOCK_C3 + self.GOOD_BLOCK_D3 \
            + self.GOOD_BLOCK_A3
        assume_na = True
        self.run_test_exception(rds_group, assume_na, RDSIntegrityFailure,
                                'This RDS group failed its integrity check:')

    def test_s04_valid_yet_disparate_blocks(self):
        """A group of RDS blocks that are not necessarily related to each other."""
        rds_group = self.GOOD_BLOCK_A1 + self.GOOD_BLOCK_B3 + self.GOOD_BLOCK_C1 \
            + self.GOOD_BLOCK_D3
        assume_na = True
        self.run_test_return(rds_group, assume_na)


if __name__ == '__main__':
    execute_test_cases()
