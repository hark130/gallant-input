"""Unit test module for validation.validate_pos_float_or_int().

Typical Usage:
    python -m test                                # Run *all* the test cases
    python -m test.unit_test                      # Run *all* the unit test cases
    python -m test.unit_test.test_validation      # Run *all* validation module test cases
    # Run just these unit tests
    python -m test.unit_test.test_validation.test_validate_pfoi
    # Run just this normal 1 unit test
    python -m test.unit_test.test_validation.test_validate_pfoi -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
from test.unit_test.root_unit_test import RootUnitTest
# Local Imports
from gallant_input.validation import validate_pos_float_or_int


class ValidatePFOIUnitTest(RootUnitTest):
    """Parent class for all validation.validate_pos_float_or_int() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        return validate_pos_float_or_int(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, validate_this: float | int, param_name: str,
                        abs_tol: float = 1e-9) -> None:
        """Common method calls for a test case expected to return.

        Args:
            validate_this: Sets the validate_this argument input.
            param_name: Sets the param_name argument input.
            abs_tol: Sets the abs_tol argument input.
        """
        self.set_test_input(validate_this, param_name, abs_tol)
        self.expect_return(None)  # This function does not return a value
        self.run_test()


class NormalValidatePFOIUnitTest(ValidatePFOIUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_float(self):
        """Valid float."""
        validate_this = 1/2
        param_name = self.test_case_data.name
        abs_tol = 1e-9
        self.run_test_return(validate_this, param_name, abs_tol)

    def test_n02_valid_int(self):
        """Valid int."""
        validate_this = 5
        param_name = self.test_case_data.name
        abs_tol = 1e-9
        self.run_test_return(validate_this, param_name, abs_tol)

    def test_n03_invalid_validate_this_type_none(self):
        """Invalid validate_this: wrong type - None."""
        validate_this = None
        param_name = self.test_case_data.name
        abs_tol = 1e-9
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(TypeError, 'data type instead of type')

    def test_n04_invalid_validate_this_type_string(self):
        """Invalid validate_this: wrong type - string."""
        validate_this = '5'
        param_name = self.test_case_data.name
        abs_tol = 1e-9
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(TypeError, 'data type instead of type')


class ErrorValidatePFOIUnitTest(ValidatePFOIUnitTest):
    """Error Test Cases."""

    def test_e01_bad_abs_tol_type_none(self):
        """Invalid abs_tol: wrong type - None.

        Verify abs_tol is pre-validated before complex validation of validate_this.
        """
        validate_this = 1/2
        param_name = self.test_case_data.name
        abs_tol = None
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(TypeError, 'The "abs_tol" argument should have been of type')

    def test_e02_bad_abs_tol_type_int(self):
        """Invalid abs_tol: wrong type - int.

        Verify abs_tol is pre-validated before complex validation of validate_this.
        """
        validate_this = 5
        param_name = self.test_case_data.name
        abs_tol = 1
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(TypeError, 'The "abs_tol" argument should have been of type')

    def test_e03_bad_abs_tol_value_negative(self):
        """Invalid abs_tol: bad value - negative."""
        validate_this = 1/2
        param_name = self.test_case_data.name
        abs_tol = -0.01
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(ValueError, 'The "abs_tol" argument *must* be > 0')

    def test_e04_bad_abs_tol_value_zero(self):
        """Invalid abs_tol: bad value - zero."""
        validate_this = 5
        param_name = self.test_case_data.name
        abs_tol = 0.0
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(ValueError, 'The "abs_tol" argument may not be 0')

    def test_e05_compound_negative_float(self):
        """Compound problem: negative float."""
        validate_this = -1/2
        param_name = self.test_case_data.name
        abs_tol = 1e-9
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(ValueError, 'argument *must* be > 0')

    def test_e06_compound_negative_int(self):
        """Compound problem: negative int."""
        validate_this = -5
        param_name = self.test_case_data.name
        abs_tol = 1e-9
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(ValueError, 'argument is not positive')


class SpecialValidatePFOIUnitTest(ValidatePFOIUnitTest):
    """Special Test Cases."""

    def test_s01_bad_param_name_type_none(self):
        """Bad param_name: wrong type - None.

        The param_name argument isn't (normally) validated.  Verify param_name is pre-validated
        before complex validation of validate_this.
        """
        validate_this = 1/2
        param_name = None
        abs_tol = 1e-9
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(TypeError, 'The "param_name" argument should have been of type')

    def test_s02_bad_param_name_type_bytes(self):
        """Bad param_name: wrong type - bytes.

        The param_name argument isn't (normally) validated.  Verify param_name is pre-validated
        before complex validation of validate_this.
        """
        validate_this = 5
        param_name = bytes(self.test_case_data.name, 'ascii')
        abs_tol = 1e-9
        self.set_test_input(validate_this, param_name, abs_tol)
        self.run_test_exception(TypeError, 'The "param_name" argument should have been of type')

    def test_s03_empty_param_name(self):
        """Empty param_name: it's fine."""
        validate_this = 5
        param_name = ''
        abs_tol = 1e-9
        self.run_test_return(validate_this, param_name, abs_tol)


if __name__ == '__main__':
    execute_test_cases()
