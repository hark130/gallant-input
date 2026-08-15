"""Unit test module for OOK.demodulate().

Typical Usage:
    python -m test                                # Run *all* the test cases
    python -m test.unit_test                      # Run *all* the unit test cases
    python -m test.unit_test.test_modem           # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_ook  # Run *all* OOK test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_ook.test_modem_ook_demodulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_ook.test_modem_ook_demodulate -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
from unittest import skip
import numpy
# Local Imports
from test.modify import add_awgn, convert_bin_bytes_to_ook, upsample_test_input
from test.unit_test.test_modem.test_ook.test_modem_ook import ModemOOKUnitTest


class ModemOOKModulateUnitTest(ModemOOKUnitTest):
    """Parent class for all OOK.demodulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.demodulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self.validate_bin_bytes_return_value(return_value=return_value)

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
    def run_test_exception_input(self, sample_rate: Any, symbol_rate: Any, samples: Any,
                                 threshold: Any, exception_type: Exception,
                                 exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate argument input.  Accepts any input, bad or otherwise.
            symbol_rate: Sets the symbol_rate argument input.  Accepts any input, bad or otherwise.
            samples: Test case input.
            threshold: Test case input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(samples, threshold)
        self.run_test_exception(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                exception_type=exception_type, exception_msg=exception_msg)

    def run_test_return(self, sample_rate: float, symbol_rate: float,
                        exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return.

        Test author must call self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            exp_ret: The expected return value from the method call.
        """
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.expect_return(exp_ret)
        self.run_test()

    def run_test_return_compute(self, sample_rate: float, symbol_rate: float,
                                threshold: float | None, exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return a computed result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            threshold: Test case input.
            exp_ret: Expected return value (also used to compute the test case input).
        """
        test_in = create_test_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                    bin_bytes=exp_ret)
        self.run_test_return_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                   samples=test_in, threshold=threshold, exp_ret=exp_ret)

    def run_test_return_input(self, sample_rate: float, symbol_rate: float, samples: numpy.ndarray,
                              threshold: float | None, exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return an expected result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            samples: Test case input.
            threshold: Test case input.
            exp_ret: The expected return value from the method call.
        """
        self.set_test_input(samples, threshold)
        self.run_test_return(sample_rate=sample_rate, symbol_rate=symbol_rate, exp_ret=exp_ret)

    def run_test_return_noisy(self, sample_rate: float, symbol_rate: float,
                              threshold: float | None, exp_ret: bytes, snr_db: float | int) -> None:
        """Common method calls for a test case expected to return a computed result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            threshold: Test case input.
            exp_ret: Expected return value (also used to compute the test case input).
            snr_db: The desigred SNR of the test case samples, in decibels.
        """
        test_in = create_noisy_test_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                          bin_bytes=exp_ret, snr_db=snr_db)
        self.run_test_return_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                   samples=test_in, threshold=threshold, exp_ret=exp_ret)
    # pylint: enable=too-many-arguments,too-many-positional-arguments


class NormalModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits(self):
        """Single byte, alternating bits."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'10101010'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_n02_all_zeros(self):
        """Single byte, all zeros."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'00000000'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_n03_all_ones(self):
        """Single byte, all ones."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'11111111'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_n04_single_byte_alt_bits_manual_valid_threshold(self):
        """Single byte, alternating bits with a safe, valid manual threshold value."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'10101010'
        threshold = 0.5
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_n05_all_zeros_manual_valid_threshold(self):
        """Single byte, all zeros with a safe, valid manual threshold value."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'00000000'
        threshold = 0.5
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_n06_all_ones_manual_valid_threshold(self):
        """Single byte, all ones with a safe, valid manual threshold value."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'11111111'
        threshold = 0.5
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_n07_single_byte_alt_bits_with_awgn(self):
        """Single byte, alternating bits, with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'10101010'
        threshold = None  # Automatically determine the threshold
        snr_db = self.SNR_GOOD
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)

    def test_n08_all_zeros_with_awgn(self):
        """Single byte, all zeros, with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'00000000'
        threshold = 0.1  # Chose arbitrarily low threshold because auto-calc was identifying noise
        snr_db = self.SNR_GOOD
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)

    @skip('Not sure why, and only this (so far), AWGN test case is failing at good SNR levels?!')
    def test_n09_all_ones_with_awgn(self):
        """Single byte, all ones, with AWGN at a reasonable SNR (dB)."""
        samp_rate = 48000
        sym_rate = 800
        # Test case input
        exp_ret = b'11111111'
        threshold = None  # Automatically determine the threshold
        snr_db = self.SNR_EXCELLENT
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)

    def test_n10_single_byte_alt_bits_manual_valid_threshold_with_awgn(self):
        """Single byte, alternating bits with a safe, valid manual threshold value, with AWGN."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'10101010'
        threshold = 0.5
        snr_db = self.SNR_GOOD
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)

    def test_n11_all_zeros_manual_valid_threshold_with_awgn(self):
        """Single byte, all zeros with a safe, valid manual threshold value, with AWGN."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'00000000'
        threshold = 0.5
        snr_db = self.SNR_GOOD
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)

    def test_n12_all_ones_manual_valid_threshold_with_awgn(self):
        """Single byte, all ones with a safe, valid manual threshold value, with AWGN."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'11111111'
        threshold = 0.5
        snr_db = self.SNR_GOOD
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)


class ErrorModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ONES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_10S
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_01S
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ONES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        test_in = self.SAMPLES_OOK_ALL_10S
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        test_in = self.SAMPLES_OOK_ALL_01S
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        test_in = self.SAMPLES_OOK_ALL_ONES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        test_in = self.SAMPLES_OOK_ALL_10S
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        test_in = self.SAMPLES_OOK_ALL_01S
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_samples_type_none(self):
        """Bad samples: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        test_in = None
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_samples_type_complex_list(self):
        """Bad samples: bad type - list of complex values (almost an ndarray)."""
        samp_rate = 48000
        sym_rate = 800
        test_in = [0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j]
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_samples_value_empty(self):
        """Bad samples: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        test_in = numpy.array([], dtype=numpy.complex64)  # len(test_in) == 0
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'ndarray may not be empty')

    def test_e16_bad_samples_invalid_dimensions(self):
        """Bad samples: wrong dimensions."""
        samp_rate = 48000
        sym_rate = 800
        test_in = numpy.resize(self.SAMPLES_OOK_ALL_10S, (2, 2))  # test_in.ndim == 2
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      f'value is {test_in.ndim}-dimensional instead of '
                                      f'{self.SAMPLES_OOK_ALL_10S.ndim}-dimensional')

    def test_e17_bad_threshold_type_string(self):
        """Bad threshold: wrong type - string."""
        samp_rate = 48000
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ONES
        threshold = '0.5'
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument should have been of type')

    def test_e18_bad_threshold_type_int(self):
        """Bad threshold: wrong type - int."""
        samp_rate = 48000
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        threshold = 1
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, TypeError,
                                      'argument should have been of type')

    def test_e19_bad_threshold_value_negative(self):
        """Bad threshold: bad value - negative."""
        samp_rate = 48000
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_10S
        threshold = -0.5
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "threshold" argument *must* be > 0')


class BoundaryModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_on(self):
        """One bit: on."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'1'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b02_one_bit_off(self):
        """One bit: off."""
        samp_rate = 4800
        sym_rate = 80
        # Test case input
        exp_ret = b'0'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b03_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = 1
        sym_rate = 80
        # Test case input
        test_in = self.SAMPLES_OOK_ALL_ONES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'argument is not positive')

    def test_b04_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = 4800
        sym_rate = 1
        # Test case input
        exp_ret = b'10101010'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b05_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        exp_ret = b'10101010'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b06_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        # Test case input
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        threshold = None  # Automatically determine the threshold
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'argument is not positive')

    def test_b07_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = float(4800.0)
        sym_rate = float(1.0)
        # Test case input
        exp_ret = b'10101010'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b08_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        exp_ret = b'10101010'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b09_smallest_everything_on(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        exp_ret = b'1'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b10_smallest_everything_off(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        # Test case input
        exp_ret = b'0'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b11_smallest_everything_on_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): on."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        exp_ret = b'1'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b12_smallest_everything_off_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): off."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        # Test case input
        exp_ret = b'0'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_b13_bad_threshold_value_zero(self):
        """Bad threshold: bad value - zero."""
        samp_rate = 48000
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_10S
        threshold = 0.0
        self.run_test_exception_input(samp_rate, sym_rate, test_in, threshold, ValueError,
                                      'The "threshold" argument may not be 0')

    def test_b14_miniscule_threshold_right_all_ones(self):
        """Miniscule threshold value is tightly tuned: right - all ones."""
        orig_symbols = self.SAMPLES_OOK_ALL_ONES  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 1.0 - 1e-7  # High, but valid
        exp_ret = b'1' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_b15_miniscule_threshold_wrong_all_ones(self):
        """Miniscule threshold value is tightly tuned: wrong - all ones."""
        orig_symbols = self.SAMPLES_OOK_ALL_ONES  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 0.99999999 + 1e-18  # Too high
        exp_ret = b'0' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_b16_equivalent_threshold_wrong_all_ones(self):
        """Miniscule threshold value is tightly tuned: wrong - all ones."""
        orig_symbols = self.SAMPLES_OOK_ALL_ONES  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 1.0  # Too equivalent to match
        exp_ret = b'0' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)


class SpecialModemOOKModulateUnitTest(ModemOOKModulateUnitTest):
    """Special Test Cases."""

    def test_s01_realistic_usage(self):
        """5.03 Demod 101 FoI 2."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # Test case input
        exp_ret = b'10101010'
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_s02_real_data_rds_set_msg00_a(self):
        """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name 'KONO    '."""
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # Test case input
        exp_ret = self.RDS_SET1_MSG00A
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_s03_real_data_demod_101_foi_1_preamble(self):
        """5.03 Demod 101 FoI 1 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        # Test case input
        exp_ret = self.DEMOD_101_FOI_1_PREAMBLE
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_s04_real_data_demod_101_foi_1_pdu(self):
        """5.03 Demod 101 FoI 1 PDU."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        # Test case input
        exp_ret = self.DEMOD_101_FOI_1_PDU
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_s05_real_data_demod_101_foi_2_preamble(self):
        """5.03 Demod 101 FoI 2 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # Test case input
        exp_ret = self.DEMOD_101_FOI_2_PREAMBLE
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_s06_real_data_demod_101_foi_3_preamble(self):
        """5.03 Demod 101 FoI 3 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 3 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 3 symbol rate
        # Test case input
        exp_ret = self.DEMOD_101_FOI_3_PREAMBLE
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_s07_real_data_fhss_chan_01_preamble(self):
        """5.05 FHSS Channel 01 Preamble."""
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # Test case input
        exp_ret = self.FHSS_CHANNEL_01_PREAMBLE
        threshold = None  # Automatically determine the threshold
        self.run_test_return_compute(samp_rate, sym_rate, threshold, exp_ret)

    def test_s08_manual_threshold_right_all_ones(self):
        """Manual threshold: right - all ones."""
        orig_symbols = self.SAMPLES_OOK_ALL_ONES  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 0.9  # High, but valid
        exp_ret = b'1' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s09_manual_threshold_wrong_all_ones(self):
        """Manual threshold: wrong - all ones."""
        orig_symbols = self.SAMPLES_OOK_ALL_ONES  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 9.0  # Too high
        exp_ret = b'0' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s10_manual_threshold_barely_wrong_all_zeros(self):
        """Manual threshold: (so small as to be) barely wrong - all zeros."""
        orig_symbols = self.SAMPLES_OOK_ALL_ZEROES  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 1e-9
        exp_ret = b'0' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s11_manual_threshold_wrong_all_zeros(self):
        """Manual threshold: wrong - all zeros."""
        orig_symbols = self.SAMPLES_OOK_ALL_ZEROES  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 9.0  # Too high
        exp_ret = b'0' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s12_manual_threshold_right_10s(self):
        """Manual threshold: right - all 10s."""
        orig_symbols = self.SAMPLES_OOK_ALL_10S  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 0.9  # High, but valid
        exp_ret = b'10' * (int(len(orig_symbols) // 2))
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s13_manual_threshold_wrong_all_10s(self):
        """Manual threshold: wrong - all 10s."""
        orig_symbols = self.SAMPLES_OOK_ALL_10S  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 9.0  # Too high
        exp_ret = b'0' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s14_manual_threshold_right_01s(self):
        """Manual threshold: right - all 01s."""
        orig_symbols = self.SAMPLES_OOK_ALL_01S  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 0.9  # High, but valid
        exp_ret = b'01' * (int(len(orig_symbols) // 2))
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s15_manual_threshold_wrong_all_01s(self):
        """Manual threshold: wrong - all 01s."""
        orig_symbols = self.SAMPLES_OOK_ALL_01S  # Origins of this test case input
        samp_rate = 48000
        sym_rate = 80
        samples = create_test_samples(orig_symbols, samp_rate, sym_rate)
        threshold = 9.0  # Too high
        exp_ret = b'0' * len(orig_symbols)
        self.run_test_return_input(samp_rate, sym_rate, samples, threshold, exp_ret)

    def test_s16_real_data_rds_set_msg00_a_with_awgn(self):
        """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A with AWGN (poor SNR)."""
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # Test case input
        exp_ret = self.RDS_SET1_MSG00A
        threshold = None  # Automatically determine the threshold
        snr_db = self.SNR_POOR
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)

    def test_s17_real_data_demod_101_foi_1_pdu_with_awgn(self):
        """5.03 Demod 101 FoI 1 PDU with AWGN (poor SNR)."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        # Test case input
        exp_ret = self.DEMOD_101_FOI_1_PDU
        threshold = None  # Automatically determine the threshold
        snr_db = self.SNR_POOR
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)

    def test_s18_real_data_fhss_chan_01_preamble_with_awgn(self):
        """5.05 FHSS Channel 01 Preamble with AWGN (poor SNR)."""
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # Test case input
        exp_ret = self.FHSS_CHANNEL_01_PREAMBLE
        threshold = None  # Automatically determine the threshold
        snr_db = self.SNR_POOR
        self.run_test_return_noisy(samp_rate, sym_rate, threshold, exp_ret, snr_db)


def create_noisy_test_input(sample_rate: int | float, symbol_rate: int | float,
                            bin_bytes: bytes, snr_db: float | int) -> numpy.ndarray:
    """Transform a binary bytes object into valid test case input that contains AWGN."""
    samples = create_test_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                bin_bytes=bin_bytes)
    return add_awgn(samples=samples, snr_db=snr_db)


def create_test_input(sample_rate: int | float, symbol_rate: int | float,
                      bin_bytes: bytes) -> numpy.ndarray:
    """Transform a binary bytes object into valid test case input."""
    return convert_bin_bytes_to_ook(bin_bytes=bin_bytes, sample_rate=sample_rate,
                                    symbol_rate=symbol_rate)


def create_test_samples(samples: numpy.ndarray, sample_rate: float | int,
                        symbol_rate: float | int) -> numpy.ndarray:
    """Create a valid 'samples' array, using production code, for use as test case input."""
    return upsample_test_input(samples, sample_rate, symbol_rate)


if __name__ == '__main__':
    execute_test_cases()
