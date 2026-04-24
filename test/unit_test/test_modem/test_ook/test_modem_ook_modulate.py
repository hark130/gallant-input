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
                self._add_test_failure('The expected array is not equal to the returned array')

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

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def run_test_exception_input(self, sample_rate: Any, symbol_rate: Any, bin_bytes: Any,
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate argument input.  Accepts any input, bad or otherwise.
            symbol_rate: Sets the symbol_rate argument input.  Accepts any input, bad or otherwise.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(bin_bytes)
        self.run_test_exception(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                exception_type=exception_type, exception_msg=exception_msg)
    # pylint: enable=too-many-arguments,too-many-positional-arguments

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

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_bin_bytes_type_none(self):
        """Bad bin_bytes: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        test_in = None
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_bin_bytes_type_string(self):
        """Bad bin_bytes: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        test_in = '10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_bin_bytes_value_empty(self):
        """Bad bin_bytes: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        test_in = b''
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'ndarray may not be empty')

    def test_e16_bad_bin_bytes_value_non_binary(self):
        """Bad bin_bytes: bad value - non-binary (AKA '...and I thought I saw a 2' -Bender)."""
        samp_rate = 48000
        sym_rate = 800
        test_in = b'101010100010101010121011110100101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'Invalid binary value detected')


class BoundaryModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_on(self):
        """One bit: on."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        test_in = b'1'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b02_one_bit_off(self):
        """One bit: off."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        test_in = b'0'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b03_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = 1
        sym_rate = 80
        # Test case input
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "samples_per_symbol" argument is not positive')

    def test_b04_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = 4800
        sym_rate = 1
        # Test case input
        test_in = b'10101010'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b05_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        test_in = b'10101010'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b06_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        # Test case input
        test_in = b'10101010'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "samples_per_symbol" argument is not positive')

    def test_b07_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = float(4800.0)
        sym_rate = float(1.0)
        # Test case input
        test_in = b'10101010'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b08_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        test_in = b'10101010'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b09_smallest_everything_on(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        test_in = b'1'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b10_smallest_everything_off(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        test_in = b'0'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b11_smallest_everything_on_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): on."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        test_in = b'1'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_b12_smallest_everything_off_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): off."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        test_in = b'0'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)


class SpecialModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Special Test Cases."""

    def test_s01_realistic_usage(self):
        """5.03 Demod 101 FoI 2."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # Test case input
        test_in = b'10101010'
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_s02_real_data_rds_set_msg00_a(self):
        """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name 'KONO    '."""
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # Test case input
        test_in = self.RDS_SET1_MSG00A
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_s03_real_data_demod_101_foi_1_preamble(self):
        """5.03 Demod 101 FoI 1 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        # Test case input
        test_in = self.DEMOD_101_FOI_1_PREAMBLE
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_s04_real_data_demod_101_foi_1_pdu(self):
        """5.03 Demod 101 FoI 1 PDU."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        # Test case input
        test_in = self.DEMOD_101_FOI_1_PDU
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_s05_real_data_demod_101_foi_2_preamble(self):
        """5.03 Demod 101 FoI 2 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # Test case input
        test_in = self.DEMOD_101_FOI_2_PREAMBLE
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_s06_real_data_demod_101_foi_3_preamble(self):
        """5.03 Demod 101 FoI 3 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 3 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 3 symbol rate
        # Test case input
        test_in = self.DEMOD_101_FOI_3_PREAMBLE
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)

    def test_s07_real_data_fhss_chan_01_preamble(self):
        """5.05 FHSS Channel 01 Preamble."""
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # Test case input
        test_in = self.FHSS_CHANNEL_01_PREAMBLE
        self.run_test_return_compute(sample_rate=samp_rate, symbol_rate=sym_rate, bin_bytes=test_in)


def compute_exp_return(sample_rate: float, symbol_rate: float, bin_bytes: bytes) -> numpy.ndarray:
    """Compute the expected return based on the test case input."""
    # LOCAL VARIABLES
    sps = int(sample_rate / symbol_rate)  # Samples per symbol
    samples = None                        # An array of the sample values
    array = None                          # The numpy.ndarray formed from the samples

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
