"""Unit test module for FSK2.modulate().

Typical Usage:
    python -m test                                 # Run *all* the test cases
    python -m test.unit_test                       # Run *all* the unit test cases
    python -m test.unit_test.test_modem            # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_fsk2  # Run *all* FSK2 test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_fsk2.test_modem_fsk2_modulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_fsk2.test_modem_fsk2_modulate -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from test.modify import convert_bin_bytes_to_array
from test.unit_test.test_modem.test_fsk2.test_modem_fsk2 import ModemFSK2UnitTest


class ModemFSK2ModulateUnitTest(ModemFSK2UnitTest):
    """Parent class for all FSK2.modulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RootUnitTest ctor."""
        # ATTRIBUTES
        self._exp_ret_ndim = None   # Expected number of dimensions for a valid return value
        self._exp_ret_shape = None  # Expected shape for a valid return value
        self._exp_ret_dtype = None  # Expected dtype for a valid return value

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.modulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self.validate_ndarray_return_details(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, sample_rate: Any, symbol_rate: Any,
                           exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate argument input.  Accepts any input, bad or otherwise.
            symbol_rate: Sets the symbol_rate argument input.  Accepts any input, bad or otherwise.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, sample_rate: float, symbol_rate: float) -> None:
        """Common method calls for a test case expected to return.

        Test author *must* call set_test_input() and *should* call set_exp_ret_values() prior
        to this method.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
        """
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.run_test()

    def run_test_return_def(self, sample_rate: float, symbol_rate: float) -> None:
        """Common method calls for a test case expected to return with default expected values.

        This method calls set_exp_ret_values() with default values but the test author
        *must* call set_test_input().

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            bin_bytes: Test case input.
        """
        self.set_exp_ret_values()
        self.run_test_return(sample_rate=sample_rate, symbol_rate=symbol_rate)

    def set_exp_ret_values(self, exp_ndim: int | None = 1, exp_shape: int | None = None,
                           exp_dtype: numpy.dtype | None = numpy.complex64) -> None:
        """Set the expect return value details for this test case.

        Use this method to set the expected details for the return value of a valid method call.
        This method does not validate the input but any non-None values should be valid.

        Args:
            exp_ndim: [OPTIONAL] Sets self._exp_ret_ndim.  A value of None skips this check.
            exp_shape: [OPTIONAL] Sets self._exp_ret_shape.  A value of None skips this check.
            exp_dtype: [OPTIONAL] Sets self._exp_ret_dtype.  A value of None skips this check.
        """
        self._exp_return = numpy.ndarray(0)  # Create an empty array for the retval data type check
        self._exp_ret_ndim = exp_ndim
        self._exp_ret_shape = exp_shape
        self._exp_ret_dtype = exp_dtype
        self._defined_expected_results = True  # Shunt around default validation framework

    def validate_ndarray_return_details(self, return_value: numpy.ndarray):
        """Completely validate numpy.ndarray return values of the tested call.

        Tests type, number of dimensions, shape, and data type as specified by the
        exp_ret_* attributes.
        """
        # LOCAL VARIABLES
        def_error = 'Array {} mismatch:'

        # VALIDATE IT
        # Type
        if self.validate_ndarray_return_type(return_value=return_value):
            # Number of dimensions
            if self._exp_ret_ndim is not None and return_value.ndim != self._exp_ret_ndim:
                self._add_test_failure(f'{def_error.format("dimension")} Expected '
                                       f'{self._exp_return.ndim} dimensions '
                                       f'but received {return_value.ndim} instead')
            # Shape
            if self._exp_ret_shape is not None and return_value.shape != self._exp_ret_shape:
                self._add_test_failure(f'{def_error.format("shape")} Expected '
                                       f'{self._exp_return.shape} shape '
                                       f'but received {return_value.shape} instead')
            # Data Type
            if self._exp_ret_dtype is not None and return_value.dtype != self._exp_ret_dtype:
                self._add_test_failure(f'{def_error.format("dtype")} Expected '
                                       f'{self._exp_return.dtype} shape '
                                       f'but received {return_value.dtype} instead')


class NormalModemFSK2ModulateUnitTest(ModemFSK2ModulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits(self):
        """Single byte, alternating bits."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_n02_all_zeros(self):
        """Single byte, all zeros."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'00000000'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_n03_all_ones(self):
        """Single byte, all ones."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'11111111'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_n04_single_byte_alt_bits_explicit_phase(self):
        """Single byte, alternating bits, explicitly set the phase."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = float(1.0)
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_n05_all_zeros_explicit_phase(self):
        """Single byte, all zeros, explicitly set the phase."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'00000000'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = float(1.5)
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_n06_all_ones_explicit_phase(self):
        """Single byte, all ones, explicitly set the phase."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'11111111'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = float(2.0)
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)


# Leave me be, Pylint.  These are test cases!
# pylint: disable=too-many-public-methods
class ErrorModemFSK2ModulateUnitTest(ModemFSK2ModulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        bits = b'10101010'
        f0 = -800 / 2
        f1 = 800 / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        bits = b'10101010'
        f0 = -800 / 2
        f1 = 800 / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_bin_bytes_type_none(self):
        """Bad bin_bytes: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        bits = None
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument should have been of type')

    def test_e14_bad_bin_bytes_type_string(self):
        """Bad bin_bytes: bad type - string."""
        samp_rate = 48000
        sym_rate = 800
        bits = '10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument should have been of type')

    def test_e15_bad_bin_bytes_value_empty(self):
        """Bad bin_bytes: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        bits = b''
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The "bin_bytes" argument may not be empty')

    def test_e16_bad_bin_bytes_value_non_binary(self):
        """Bad bin_bytes: bad value - non-binary (AKA '...and I thought I saw a 2' -Bender)."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'101010100010101010121011110100101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'Invalid binary value detected')

    def test_e17_bad_freq0_type_none(self):
        """Bad freq0: wrong type - None."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'10101010'
        f0 = None
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e18_bad_freq0_type_string(self):
        """Bad freq0: wrong type - string."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'10101010'
        f0 = str(-sym_rate / 2)
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e19_bad_freq1_type_none(self):
        """Bad freq1: wrong type - None."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = None
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e20_bad_freq1_type_string(self):
        """Bad freq1: wrong type - string."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = str(sym_rate / 2)
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument must be a')

    def test_e21_bad_phase_type_int(self):
        """Bad phase: wrong type - int."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = int(1)
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, TypeError,
                                'argument should have been of type')

    def test_e22_bad_phase_value_negative(self):
        """Bad phase: value - negative."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = -1.0
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'value may not be negative')

    def test_e23_bad_phase_value_too_large(self):
        """Bad phase: value - too large."""
        samp_rate = 48000
        sym_rate = 800
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = numpy.pi * 10
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'value may not be greater than')


class BoundaryModemFSK2ModulateUnitTest(ModemFSK2ModulateUnitTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_on(self):
        """One bit: on."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'1'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b02_one_bit_off(self):
        """One bit: off."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'0'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b03_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = 1
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'argument is not positive')

    def test_b04_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = 4800
        sym_rate = 1
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b05_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b06_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'argument is not positive')

    def test_b07_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = float(4800.0)
        sym_rate = float(1.0)
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b08_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b09_smallest_everything_on(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        bits = b'1'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b10_smallest_everything_off(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        bits = b'0'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b11_smallest_everything_on_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): on."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        bits = b'1'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b12_smallest_everything_off_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): off."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        bits = b'0'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b13_phase_bounds_large_negative(self):
        """Phase bounds test: large negative value."""
        samp_rate = 48000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = numpy.pi * -10
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'value may not be negative')

    def test_b14_phase_bounds_barely_negative(self):
        """Phase bounds test: barely negative value."""
        samp_rate = 48000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = -1.0 * 1e-128
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'value may not be negative')

    def test_b15_phase_bounds_barely_valid_zero(self):
        """Phase bounds test: barely valid at 0."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = float(0.0)
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b16_phase_bounds_barely_valid_two_pi(self):
        """Phase bounds test: barely valid at 2π."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = 2 * numpy.pi
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b17_phase_bounds_barely_over_two_pi(self):
        """Phase bounds test: barely > 2π."""
        samp_rate = 48000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = (2 * numpy.pi) + 1e-8
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'value may not be greater than')

    def test_b18_f0_vs_f1_same(self):
        """Freq0 vs Freq1: f0 == f1."""
        samp_rate = 48000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = f0
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The deviation between')

    def test_b18_f0_vs_f1_almost_the_same(self):
        """Freq0 vs Freq1: math.isclose(f0, f1)."""
        samp_rate = 48000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = f0 + 1e-8
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The deviation between')

    def test_b19_f0_vs_f1_almost_half_sym_rate_separation(self):
        """Freq0 vs Freq1: f1 == f0 + (symbol rate / 2) - a little bit."""
        samp_rate = 48000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = f0 + (sym_rate / 2) - 1e-8
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_exception(samp_rate, sym_rate, ValueError,
                                'The deviation between')

    def test_b20_f0_vs_f1_half_sym_rate_separation(self):
        """Freq0 vs Freq1: f1 == f0 + (symbol rate / 2) + a little bit."""
        samp_rate = 48000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = f0 + (sym_rate / 2) + 1e-128
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_b21_f0_vs_f1_very_different(self):
        """Freq0 vs Freq1: f0 is far from f1."""
        samp_rate = 480000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -samp_rate * sym_rate
        f1 = samp_rate * sym_rate
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)
# pylint: enable=too-many-public-methods


class SpecialModemFSK2ModulateUnitTest(ModemFSK2ModulateUnitTest):
    """Special Test Cases."""

    def test_s01_realistic_usage(self):
        """5.03 Demod 101 FoI 2."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s02_real_data_rds_set_msg00_a(self):
        """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name 'KONO    '."""
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # Test case input
        bits = self.RDS_SET1_MSG00A
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s03_real_data_demod_101_foi_1_preamble(self):
        """5.03 Demod 101 FoI 1 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        # Test case input
        bits = self.DEMOD_101_FOI_1_PREAMBLE
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s04_real_data_demod_101_foi_1_pdu(self):
        """5.03 Demod 101 FoI 1 PDU."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        # Test case input
        bits = self.DEMOD_101_FOI_1_PDU
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s05_real_data_demod_101_foi_2_preamble(self):
        """5.03 Demod 101 FoI 2 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # Test case input
        bits = self.DEMOD_101_FOI_2_PREAMBLE
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s06_real_data_demod_101_foi_3_preamble(self):
        """5.03 Demod 101 FoI 3 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 3 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 3 symbol rate
        # Test case input
        bits = self.DEMOD_101_FOI_3_PREAMBLE
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s07_real_data_fhss_chan_01_preamble(self):
        """5.05 FHSS Channel 01 Preamble."""
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # Test case input
        bits = self.FHSS_CHANNEL_01_PREAMBLE
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s08_f0_vs_f1_both_neg(self):
        """Freq0 vs Freq1: valid deviation but both f0 and f1 are negative."""
        samp_rate = 480000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -samp_rate * sym_rate * 2
        f1 = -samp_rate * sym_rate
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s09_f0_vs_f1_but_f1_is_lower(self):
        """Freq0 vs Freq1: valid deviation but f1 < f0."""
        samp_rate = 480000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = sym_rate / 2
        f1 = -sym_rate / 2
        phase = None
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)

    def test_s10_override_phase_with_default(self):
        """Override phase with default value."""
        samp_rate = 480000
        sym_rate = 80
        # Test case input
        bits = b'10101010'
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = 0.0
        self.set_test_input(bits, f0, f1, phase)
        self.run_test_return_def(sample_rate=samp_rate, symbol_rate=sym_rate)


if __name__ == '__main__':
    execute_test_cases()
