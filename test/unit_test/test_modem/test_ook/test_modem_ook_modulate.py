"""Unit test module for OOK.get_block_data().

Typical Usage:
    python -m test                                # Run *all* the test cases
    python -m test.unit_test                      # Run *all* the unit test cases
    python -m test.unit_test.test_modem           # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_ook  # Run *all* OOK test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_ook.test_modem_ook_modulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_ook.test_modem_ook_modulate -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits
from gallant_input.validation import validate_binary_bytes
from test.unit_test.test_modem.test_ook.test_modem_ook import ModemOOKUnitTest


class ModemOOKModulateUnitTest(ModemOOKUnitTest):
    """Parent class for all OOK.modulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.modulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        # LOCAL VARIABLES
        def_error = 'Array {} mismatch:'

        # VALIDATE IT
        # Type
        if not isinstance(return_value, type(self._exp_return)):
            self._add_test_failure(f'Expected type {type(self._exp_return)} '
                                   f'but it was of type {type(return_value)}')
        else:
            # Number of dimensions
            if return_value.ndim != self._exp_return.ndim:
                self._add_test_failure(f'{def_error.format("dimension")} Expected '
                                       f'{self._exp_return.ndim} dimensions '
                                       f'but received {return_value.ndim} instead')
            # Shape
            if return_value.shape != self._exp_return.shape:
                self._add_test_failure(f'{def_error.format("shape")} Expected '
                                       f'{self._exp_return.shape} shape '
                                       f'but received {return_value.shape} instead')
            # Data Type
            if return_value.dtype != self._exp_return.dtype:
                self._add_test_failure(f'{def_error.format("dtype")} Expected '
                                       f'{self._exp_return.dtype} shape '
                                       f'but received {return_value.dtype} instead')
            # Final Catch All
            if not numpy.array_equal(return_value, self._exp_return):
                self._add_test_failure(f'The expected array is not equal to the returned array')

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, sample_rate: Any, symbol_rate: Any,
                           exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            rds_block: Sets the rds_block argument input.  Accepts any input, including bad input.
            block_id: Sets the block_id argument input.  Accepts any input, including bad input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, sample_rate: float, symbol_rate: float,
                        exp_ret: numpy.ndarray) -> None:
        """Common method calls for a test case expected to return.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            exp_ret: The expected return value from the method call.
        """
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.expect_return(exp_ret)
        self.run_test()

    def run_test_return_compute(self, sample_rate: float, symbol_rate: float,
                                bin_bytes: bytes) -> None:
        """Common method calls for a test case expected to return a computed result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            bin_bytes: Test case input.
        """
        exp_ret = compute_exp_return(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                     bin_bytes=bin_bytes)
        self.run_test_return_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                   bin_bytes=bin_bytes, exp_ret=exp_ret)

    def run_test_return_input(self, sample_rate: float, symbol_rate: float, bin_bytes: bytes,
                              exp_ret: numpy.ndarray) -> None:
        """Common method calls for a test case expected to return an expected result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            bin_bytes: Test case input.
            exp_ret: The expected return value from the method call.
        """
        self.set_test_input(bin_bytes)
        self.run_test_return(sample_rate=sample_rate, symbol_rate=symbol_rate, exp_ret=exp_ret)


class NormalModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits(self):
        """Single byte, alternating bits."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        test_in = b'10101010'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_n02_all_zeros(self):
        """Single byte, all zeros."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        test_in = b'00000000'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_n03_all_ones(self):
        """Single byte, all ones."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        test_in = b'11111111'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)


class ErrorModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Error Test Cases."""

    def test_e01_(self):
        """."""


class ErrorModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Error Test Cases."""

    def test_b01_(self):
        """."""


class SpecialModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Special Test Cases."""

    def test_s01_realistic_usage(self):
        """5.03 Demod 101 FoI 2."""
        samp_rate = 48000  # 5.03 Demod 101 FoI 2
        sym_rate = 800     # 5.03 Demod 101 FoI 2
        # Test case input
        test_in = b'10101010'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)


def compute_exp_return(sample_rate: float, symbol_rate: float, bin_bytes: bytes) -> numpy.ndarray:
    """Compute the expected return based on the test case input."""
    # LOCAL VARIABLES
    sps = int(sample_rate / symbol_rate)  # Samples per symbol
    samples = None                        # An array of the sample values
    array = None                          # The numpy.ndarray formed from the samples
    bin_array = convert_ascii_bin_bytes_to_bits(bin_bytes)

    # COMPUTE IT
    samples = []
    for bin_byte in bin_bytes:
        samples += [int(chr(bin_byte))] * sps
    samples = b''.join([bytes(str(sample), 'ascii') for sample in samples])
    array = convert_ascii_bin_bytes_to_bits(samples).astype(numpy.complex64)

    # DONE
    return array


if __name__ == '__main__':
    execute_test_cases()
