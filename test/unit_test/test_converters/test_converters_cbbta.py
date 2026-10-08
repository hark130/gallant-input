"""Unit test module for converters.convert_bin_bytes_to_ascii().

Typical Usage:
    python -m test                                # Run *all* the test cases
    python -m test.unit_test                      # Run *all* the unit test cases
    python -m test.unit_test.test_converters      # Run *all* converters module test cases
    # Run just these unit tests
    python -m test.unit_test.test_converters.test_converters_cbbta
    # Run just this normal 1 unit test
    python -m test.unit_test.test_converters.test_converters_cbbta -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
from test.unit_test.root_unit_test import RootUnitTest
# Local Imports
from gallant_input.converters import convert_ascii_to_bin_bytes, convert_bin_bytes_to_ascii
from test.modify import convert_bytes_to_str  # Double-do legacy function


class ConvertersCBBTAUnitTest(RootUnitTest):
    """Parent class for all converters.convert_bin_bytes_to_ascii() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        return convert_bin_bytes_to_ascii(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def calc_exp_return(self, binary: bytes, clean_it: bool) -> None:
        """Double-do function replicating the tested functionality.

        Args:
            binary: Test case input for the argument of the same name.
            clean_it: Test case input for the argument of the same name.
        """
        exp_ret = convert_bytes_to_str(binary, clean_it)
        self.expect_return(exp_ret)

    def run_test_exception(self, binary: Any, clean_it: Any,
                           exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            binary: Test case input for the argument of the same name.
            clean_it: Test case input for the argument of the same name.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(binary, clean_it)
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, binary: bytes, clean_it: bool) -> None:
        """Common method calls for a test case expected to return.

        Args:
            binary_in: Test case input for the argument of the same name.
            clean_it: Test case input for the argument of the same name.
        """
        self.set_test_input(binary, clean_it)
        self.calc_exp_return(binary, clean_it)
        self.run_test()


class NormalConvertersCBBTAUnitTest(ConvertersCBBTAUnitTest):
    """Normal Test Cases."""

    def test_n01_sanitized_input_no_clean(self):
        """Valid bytes; no cleaning."""
        binary = b'01010111011010000110111100111111'  # Who?
        clean_it = False
        self.run_test_return(binary, clean_it)

    def test_n02_sanitized_input_clean_it(self):
        """Valid bytes; no cleaning."""
        binary = b'01010111011010000110111100111111'  # Who?
        clean_it = True
        self.run_test_return(binary, clean_it)


class ErrorConvertersCBBTAUnitTest(ConvertersCBBTAUnitTest):
    """Error Test Cases."""

    def test_e01_invalid_type_binary_none(self):
        """Invalid type: binary (None)."""
        binary = None
        clean_it = False
        exception_type = TypeError
        exception_msg = self.format_except_msg_invalid_type(binary, 'binary', type(b''))
        self.run_test_exception(binary, clean_it, exception_type, exception_msg)

    def test_e02_invalid_type_binary_str(self):
        """Invalid type: binary (string)."""
        binary = '01010111011010000110111100111111'  # Who?
        clean_it = False
        exception_type = TypeError
        exception_msg = self.format_except_msg_invalid_type(binary, 'binary', type(b''))
        self.run_test_exception(binary, clean_it, exception_type, exception_msg)

    def test_e03_invalid_type_clean_it_none(self):
        """Invalid type: clean_it (None)."""
        binary = b'01010111011010000110111100111111'  # Who?
        clean_it = None
        exception_type = TypeError
        exception_msg = self.format_except_msg_invalid_type(clean_it, 'clean_it', type(True))
        self.run_test_exception(binary, clean_it, exception_type, exception_msg)

    def test_e04_invalid_type_clean_it_str(self):
        """Invalid type: clean_it (string)."""
        binary = b'01010111011010000110111100111111'  # Who?
        clean_it = 'True'
        exception_type = TypeError
        exception_msg = self.format_except_msg_invalid_type(clean_it, 'clean_it', type(True))
        self.run_test_exception(binary, clean_it, exception_type, exception_msg)

    def test_e05_invalid_value_binary_non_binary(self):
        """Invalid value: binary (non-binary).

        'It was just a dream, Bender. There's no such thing as two.' - Fry
        """
        binary = b'01010111011010200110111100111111'
        clean_it = False
        exception_type = ValueError
        exception_msg = self.format_except_msg_non_binary_val('binary')
        self.run_test_exception(binary, clean_it, exception_type, exception_msg)


class BoundaryConvertersCBBTAUnitTest(ConvertersCBBTAUnitTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_off(self):
        """Non-byte aligned input: One bit; 0."""
        binary = b'0'
        clean_it = False
        self.run_test_return(binary, clean_it)

    def test_b02_one_bit_on(self):
        """Non-byte aligned input: One bit; 1."""
        binary = b'1'
        clean_it = False
        self.run_test_return(binary, clean_it)

    def test_b03_seven_bits(self):
        """Non-byte aligned input: Seven bits."""
        binary = b'01010111011010000110111100111111'[:7]  # Who?
        clean_it = False
        self.run_test_return(binary, clean_it)

    def test_b04_nine_bits(self):
        """Non-byte aligned input: Nine bits."""
        binary = b'01010111011010000110111100111111'[:9]  # Who?
        clean_it = False
        self.run_test_return(binary, clean_it)


class SpecialConvertersCBBTAUnitTest(ConvertersCBBTAUnitTest):
    """Special Test Cases."""

    def test_s01_binary_empty_but_valid(self):
        """Empty binary bytes objects are permitted."""
        binary = b''
        clean_it = False
        self.run_test_return(binary, clean_it)

    def test_s02_binary_empty_but_valid_clean_it(self):
        """Empty binary bytes objects are permitted; clean it."""
        binary = b''
        clean_it = True
        self.run_test_return(binary, clean_it)

    def test_s03_non_printable_hex_escape(self):
        """Non-printable characters: hex escape."""
        clean_it = False
        binary = convert_ascii_to_bin_bytes('Hello\x00\x01World\xff?', False)
        self.run_test_return(binary, clean_it)

    def test_s04_non_printable_hex_escape_clean_it(self):
        """Non-printable characters: hex escape; clean it."""
        clean_it = True
        binary = convert_ascii_to_bin_bytes('Hello\x00\x01World\xff?', False)
        self.run_test_return(binary, clean_it)

    def test_s05_printable_whitespace(self):
        """Printable characters: permitted whitespace."""
        clean_it = False
        binary = convert_ascii_to_bin_bytes('\tHello World?\n!!!', False)
        self.run_test_return(binary, clean_it)

    def test_s06_printable_whitespace_clean_it(self):
        """Printable characters: permitted whitespace; clean it."""
        clean_it = True
        binary = convert_ascii_to_bin_bytes('\tHello World?\n!!!', False)
        self.run_test_return(binary, clean_it)

    def test_s07_mix_it_all(self):
        """Printable and non-printable characters."""
        clean_it = False
        binary = convert_ascii_to_bin_bytes('\tHello\x00\x01World\xff?\n!!!', False)
        self.run_test_return(binary, clean_it)

    def test_s08_mix_it_all_clean_it(self):
        """Printable and non-printable characters; clean it."""
        clean_it = True
        binary = convert_ascii_to_bin_bytes('\tHello\x00\x01World\xff?\n!!!', False)
        self.run_test_return(binary, clean_it)


if __name__ == '__main__':
    execute_test_cases()
