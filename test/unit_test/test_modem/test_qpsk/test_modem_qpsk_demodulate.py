"""Unit test module for QPSK.demodulate().

Typical Usage:
    python -m test                                 # Run *all* the test cases
    python -m test.unit_test                       # Run *all* the unit test cases
    python -m test.unit_test.test_modem            # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_qpsk  # Run *all* QPSK test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_qpsk.test_modem_qpsk_demodulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_qpsk.test_modem_qpsk_demodulate -k n01
"""

# Standard Imports
from pathlib import Path
from typing import Any
# Third Party Imports
from numpy.typing import DTypeLike
from tediousstart.tediousstart import execute_test_cases
from unittest import skip
import numpy
# Local Imports
from gallant_input.modem.constants import BPSK_MAP, QPSK_MAP
from gallant_input.modem.matched_filter import MatchedFilter
from gallant_input.synch.costas_loop import CostasLoop
from test.modify import add_awgn, convert_bin_bytes_to_qpsk, generate_bin_bytes, rotate_mapping
from test.unit_test.test_modem.test_qpsk.test_modem_qpsk import ModemQPSKUnitTest


class ModemQPSKDemodulateUnitTest(ModemQPSKUnitTest):
    """Parent class for all QPSK.demodulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.demodulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self.validate_bin_bytes_return_value(return_value=return_value)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_qpsk_ctor_args() *and* self.set_test_input().

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_exception_input(self, samples: Any, filt: Any,
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_qpsk_ctor_args().

        Args:
            samples: Test case input for the argument of the same name.
            filt: Test case input for the argument of the same name.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(samples, filt)
        self.run_test_exception(exception_type=exception_type, exception_msg=exception_msg)

    def run_test_return(self, sample_rate: float, symbol_rate: float,
                        carrier_recovery: CostasLoop | None, mapper: dict[int, complex] | None,
                        exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return.

        Test author must call self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate ctor config argument input.
            symbol_rate: Sets the symbol_rate ctor config argument input.
            carrier_recovery: Sets the carrier_recovery ctor config argument input.
            mapper: Sets the mapper ctor config argument input.
            exp_ret: The expected return value from the method call.
        """
        self.set_qpsk_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                carrier_recovery=carrier_recovery, mapper=mapper)
        self.expect_return(exp_ret)
        self.run_test()

    def run_test_return_compute(self, sample_rate: float, symbol_rate: float,
                                carrier_recovery: CostasLoop | None,
                                mapper: dict[int, complex] | None, exp_ret: bytes,
                                filt: MatchedFilter) -> None:
        """Common method calls for a test case expected to return a computed result.

        This method computes the 'samples' test case input.

        Args:
            sample_rate: Sets the sample_rate ctor config argument input.
            symbol_rate: Sets the symbol_rate ctor config argument input.
            carrier_recovery: Sets the carrier_recovery ctor config argument input.
            mapper: Sets the mapper ctor config argument input.
            exp_ret: Expected return value (also used to compute the 'samples' test case input).
            filt: Test case input for the argument of the same name.
        """
        test_in = create_test_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                    bin_bytes=exp_ret, bit_map=mapper)
        self.run_test_return_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                   carrier_recovery=carrier_recovery, mapper=mapper,
                                   samples=test_in, filt=filt, exp_ret=exp_ret)

    def run_test_return_input(self, sample_rate: float, symbol_rate: float,
                              carrier_recovery: CostasLoop | None,
                              mapper: dict[int, complex] | None, samples: numpy.ndarray,
                              filt: MatchedFilter, exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return an expected result.

        Args:
            sample_rate: Sets the sample_rate ctor config argument input.
            symbol_rate: Sets the symbol_rate ctor config argument input.
            carrier_recovery: Sets the carrier_recovery ctor config argument input.
            mapper: Sets the mapper ctor config argument input.
            samples: Test case input for the argument of the same name.
            filt: Test case input for the argument of the same name.
            exp_ret: The expected return value from the method call.
        """
        self.set_test_input(samples, filt)
        self.run_test_return(sample_rate=sample_rate, symbol_rate=symbol_rate,
                             carrier_recovery=carrier_recovery, mapper=mapper, exp_ret=exp_ret)

    def run_test_return_noisy(self, sample_rate: float, symbol_rate: float,
                              carrier_recovery: CostasLoop | None,
                              mapper: dict[int, complex] | None,
                              exp_ret: bytes, snr_db: float | int,
                              filt: MatchedFilter) -> None:
        """Common method calls for a test case expected to return a computed result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            exp_ret: Expected return value (also used to compute the test case input).
            snr_db: The desigred SNR of the test case samples, in decibels.
            filt: [OPTIONAL] Test case input.
            mapper: [OPTIONAL] Test case input.
        """
        test_in = create_noisy_test_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                          bin_bytes=exp_ret, snr_db=snr_db, bit_map=mapper)
        self.run_test_return_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                   carrier_recovery=carrier_recovery, mapper=mapper,
                                   samples=test_in, filt=filt, exp_ret=exp_ret)


class NormalModemQPSKDemodulateUnitTest(ModemQPSKDemodulateUnitTest):
    """Normal Test Cases."""

# NOTES:
# - Remove short binary test cases (see: QPSK.modulate() unit test cases) or swap the static test input for random binary
# - Keep AWGN test cases (but swap static binary for random input)

    def test_n01_single_word_random_bits(self):
        """Single byte of random bits."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=1*8)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_n02_half_word_random_bits(self):
        """Two bytes of random bits."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=2*8)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_n03_double_word_random_bits(self):
        """Four bytes of random bits."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=4*8)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_n04_quad_word_random_bits(self):
        """Eight bytes of random bits."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=8*8)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_n05_quad_word_repeating_all_symbols(self):
        """Repeating all symbols for eight bytes."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = QPSK_MAP  # Necessary to right-size the binary input
        # Setup
        bps = 2                                    # Bits per symbol
        repeat = int(8 * 8 / (bps * len(mapper)))  # Number of repeats
        # QPSK().demodulate() input
        bits = b''.join([bytes(f'{key:02b}', 'ascii') for key in QPSK_MAP]) * repeat
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_n06_random_bits(self):
        """Random bits."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_n07_random_bits_with_awgn(self):
        """Random bits with AWGN at a reasonable SNR (dB)."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # Setup
        snr_db = self.SNR_POOR
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_noisy(sample_rate=samp_rate, symbol_rate=sym_rate,
                                   carrier_recovery=carr_rec, mapper=mapper, exp_ret=bits,
                                   snr_db=snr_db, filt=filt)


class ErrorModemQPSKDemodulateUnitTest(ModemQPSKDemodulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        # QPSKConfig() input
        samp_rate = None
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        # QPSKConfig() input
        samp_rate = '48000'
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        # QPSKConfig() input
        samp_rate = 0
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        # QPSKConfig() input
        samp_rate = -48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        # QPSKConfig() input
        samp_rate = float(0.0)
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        # QPSKConfig() input
        samp_rate = float(-48000.0)
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = None
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = '800'
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 0
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = -800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = float(0.0)
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = float(-800.0)
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_carrier_recover_type_dict(self):
        """Bad sample rate: bad type - dict."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = QPSK_MAP  # Represents flipped config arguments
        mapper = None        # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, NotImplementedError,
                                      'Received an unsupported "carrier recovery" object')

    def test_e14_bad_carrier_recovery_type_complex_str(self):
        """Bad carrier_recover: bad type - string."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = 'CostasLoop'
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, NotImplementedError,
                                      'Received an unsupported "carrier recovery" object')

    def test_e15_bad_carrier_recovery_content_loop_band(self):
        """Bad carrier_recover: bad content - loop bandwidth."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = CostasLoop(loop_bandwidth='0.01')
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument should have been of type')

    def test_e16_bad_carrier_recovery_content_damp_fact(self):
        """Bad carrier_recover: bad content - damping factor."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = CostasLoop(damping_factor='0.707')
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument should have been of type')

    def test_e17_bad_mapper_type_list(self):
        """Bad mapper: bad type - list."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = list(QPSK_MAP.values())  # Should be a dict
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'The "mapper" argument should have been of type')

    def test_e18_bad_mapper_value_barely_a_map(self):
        """Bad mapper: bad value - only one entry from a quad mapping."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = {key: QPSK_MAP[key] for key in list(QPSK_MAP)[:1]}  # Only one entry from QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e19_bad_mapper_value_not_a_quad_map(self):
        """Bad mapper: bad value - Binary Phase-Shift Keying (BPSK) mapping."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = BPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e20_bad_mapper_value_almost_a_quad_map(self):
        """Bad mapper: bad value - one shy of a quad mapping."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = {key: QPSK_MAP[key] for key in list(QPSK_MAP)[:len(QPSK_MAP) - 1]}  # One shy
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e21_bad_samples_type_none(self):
        """Bad samples: bad type - None."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = None
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument should have been of type')

    def test_e22_bad_samples_type_complex_list(self):
        """Bad samples: bad type - list of complex values (almost an ndarray)."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = [0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j]
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument should have been of type')

    def test_e23_bad_samples_value_empty(self):
        """Bad samples: bad value - empty."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = numpy.array([], dtype=numpy.complex64)  # len(samples) == 0
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'ndarray may not be empty')

    def test_e24_bad_samples_invalid_dimensions(self):
        """Bad samples: wrong dimensions."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = numpy.resize(self.SAMPLES_OOK_ALL_10S, (2, 2))  # samples.ndim == 2
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      f'value is {samples.ndim}-dimensional instead of '
                                      f'{self.SAMPLES_OOK_ALL_10S.ndim}-dimensional')

    def test_e25_bad_filt_type_none(self):
        """Bad filt: bad type - None."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = None  # As opposed to MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument should have been of type')

    def test_e26_bad_filt_type_str(self):
        """Bad filt: bad type - string."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.RRC.name  # As opposed to MatchedFilter.RRC
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument should have been of type')

    def test_e27_bad_filt_type_int(self):
        """Bad filt: bad type - int."""
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_10S  # Just to get a valid array
        filt = MatchedFilter.RECT_FIR.real  # As opposed to MatchedFilter.RECT_FIR
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, TypeError,
                                      'argument should have been of type')


class BoundaryModemQPSKDemodulateUnitTest(ModemQPSKDemodulateUnitTest):
    """Boundary Test Cases."""

    # Template min-number-of-symbols-not-met ValueError exception message template
    template_nsym_exc = 'Requires at least 4 symbols to cluster but received {}'

    def test_b01_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        # QPSKConfig() input
        samp_rate = 1
        sym_rate = 80
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_ONES  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'argument is not positive')

    def test_b02_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        # QPSKConfig() input
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        samples = self.SAMPLES_OOK_ALL_ZEROES  # Just to get a valid array
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      'argument is not positive')

    def test_b03_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        # QPSKConfig() input
        samp_rate = 4800
        sym_rate = 1
        carr_rec = None
        mapper = QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_b04_lowest_symbol_rate_floats(self):
        """Smallest valid symbol rate (as floats)."""
        # QPSKConfig() input
        samp_rate = float(4800.0)
        sym_rate = float(1.0)
        carr_rec = None
        mapper = QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_b05_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        # QPSKConfig() input
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        mapper = QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_b06_lowest_samples_per_symbol_floats(self):
        """Smallest valid sample rate and symbol rate (as floats)."""
        # QPSKConfig() input
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        carr_rec = None
        mapper = QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_b07_inadequate_min_num_syms_one(self):
        """Minimum number of symbols not met: one (requires four)."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = QPSK_MAP  # Necessary to create the samples
        # QPSK().demodulate() input
        num_syms = 1       # The number of symbols to generate for this test case
        bits = generate_bin_bytes(num_bits=self.bits_per_symbol*num_syms)  # Source binary
        samples = convert_bin_bytes_to_qpsk(bin_bytes=bits, sample_rate=samp_rate,
                                            symbol_rate=sym_rate, bit_map=mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      self.template_nsym_exc.format(num_syms))

    def test_b08_barely_inadequate_min_num_syms_three(self):
        """Minimum number of symbols not met: three (requires four)."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = QPSK_MAP  # Necessary to create the samples
        # QPSK().demodulate() input
        num_syms = 3       # The number of symbols to generate for this test case
        bits = generate_bin_bytes(num_bits=self.bits_per_symbol*num_syms)  # Source binary
        samples = convert_bin_bytes_to_qpsk(bin_bytes=bits, sample_rate=samp_rate,
                                            symbol_rate=sym_rate, bit_map=mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(samples, filt, ValueError,
                                      self.template_nsym_exc.format(num_syms))

    def test_b09_barely_met_min_num_syms_four(self):
        """Barely met the minimum number of symbols: four."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        num_syms = 4       # The number of symbols to generate for this test case
        bits = generate_bin_bytes(num_bits=self.bits_per_symbol*num_syms)
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_b10_barely_exceeded_min_num_syms_five(self):
        """Barely exceeded the minimum number of symbols: five (requires at least four)."""
        # QPSKConfig() input
        samp_rate = 32000  # GNU Radio tutorial example settings
        sym_rate = 8000    # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None      # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        num_syms = 5       # The number of symbols to generate for this test case
        bits = generate_bin_bytes(num_bits=self.bits_per_symbol*num_syms)
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)


class SpecialModemQPSKDemodulateUnitTest(ModemQPSKDemodulateUnitTest):
    """Special Test Cases."""

    def test_s01_weird_mapper_rotated_30_deg(self):
        """Weird mapper: rotated 30° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 6)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s02_weird_mapper_rotated_45_deg(self):
        """Weird mapper: rotated 45° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 4)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s03_weird_mapper_rotated_60_deg(self):
        """Weird mapper: rotated 60° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 3)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s04_weird_mapper_rotated_90_deg(self):
        """Weird mapper: rotated 90° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 2)  # Imaginary values instead of real
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s05_weird_mapper_rotated_120_deg(self):
        """Weird mapper: rotated 120° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi / 3)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s06_weird_mapper_rotated_135_deg(self):
        """Weird mapper: rotated 135° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 4)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s07_weird_mapper_rotated_150_deg(self):
        """Weird mapper: rotated 150° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 6)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s08_weird_mapper_rotated_180_deg(self):
        """Weird mapper: rotated 180° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi)  # Flipped position
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s09_weird_mapper_rotated_210_deg(self):
        """Weird mapper: rotated 210° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 6)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s10_weird_mapper_rotated_225_deg(self):
        """Weird mapper: rotated 225° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 4)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s11_weird_mapper_rotated_240_deg(self):
        """Weird mapper: rotated 240° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 4 * numpy.pi / 3)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s12_weird_mapper_rotated_270_deg(self):
        """Weird mapper: rotated 270° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 2)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s13_weird_mapper_rotated_300_deg(self):
        """Weird mapper: rotated 300° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 3)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s14_weird_mapper_rotated_315_deg(self):
        """Weird mapper: rotated 315° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 4)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s15_weird_mapper_rotated_330_deg(self):
        """Weird mapper: rotated 330° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 11 * numpy.pi / 6)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s16_weird_mapper_rotated_360_deg(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change).

        Binary mapping rotated away from the real axis on the complex plane.
        """
        # QPSKConfig() input
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi)
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    @skip('This test case is invalid until GAIN-26 is completed')
    def test_s17_carrier_recovery_costas_loop(self):
        """Random bits; carrier recovery: Costas Loop."""
        # QPSKConfig() input
        samp_rate = 4800
        sym_rate = 80
        carr_rec = CostasLoop()
        mapper = None            # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=128)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    @skip('This test case is invalid until GAIN-26 is completed')
    def test_s18_carrier_recovery_of_random_bits_with_awgn(self):
        """Random bits with AWGN at a reasonable SNR (dB) using a Costas Loop."""
        # QPSKConfig() input
        samp_rate = 4800
        sym_rate = 80
        carr_rec = CostasLoop()
        mapper = None            # Defaults to QPSK_MAP
        # Setup
        snr_db = self.SNR_POOR
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=128)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_noisy(sample_rate=samp_rate, symbol_rate=sym_rate,
                                   carrier_recovery=carr_rec, mapper=mapper, exp_ret=bits,
                                   snr_db=snr_db, filt=filt)

    @skip('This test case is invalid until GAIN-26 is completed')
    def test_s19_everything_everywhere_all_at_once(self):
        """Random AWGN bits, at a reasonable SNR (dB), using a Costas Loop and rectangular FIR."""
        # QPSKConfig() input
        samp_rate = 4800
        sym_rate = 80
        carr_rec = CostasLoop()
        mapper = None            # Defaults to QPSK_MAP
        # Setup
        snr_db = self.SNR_POOR
        # QPSK().demodulate() input
        bits = generate_bin_bytes(num_bits=256)  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.RECT_FIR
        self.run_test_return_noisy(sample_rate=samp_rate, symbol_rate=sym_rate,
                                   carrier_recovery=carr_rec, mapper=mapper, exp_ret=bits,
                                   snr_db=snr_db, filt=filt)

    def test_s20_one_symbol_repeated_zero(self):
        """Exclusively one symbol repeated: 00."""
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None       # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = b'00' * 128  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s21_one_symbol_repeated_one(self):
        """Exclusively one symbol repeated: 01."""
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None       # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = b'01' * 128  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s22_one_symbol_repeated_two(self):
        """Exclusively one symbol repeated: 10."""
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None       # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = b'10' * 128  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s23_one_symbol_repeated_three(self):
        """Exclusively one symbol repeated: 11."""
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None       # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = b'11' * 128  # Expected ret value computes the 'samples' input
        filt = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, mapper, bits, filt)

    def test_s24_odd_binary_len_leading_zero(self):
        """Odd length input binary expects zero padding: leading 0.

        The resulting demodulated binary will always be even.
        """
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None       # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = b'0' + generate_bin_bytes(num_bits=254)  # len(bits) == 255
        filt = MatchedFilter.NONE
        # Test case setup
        exp_ret = bits + b'0'  # QPSK output is always even
        samples = create_test_input(sample_rate=samp_rate, symbol_rate=sym_rate,
                                    bin_bytes=bits, bit_map=mapper)
        self.run_test_return_input(sample_rate=samp_rate, symbol_rate=sym_rate,
                                   carrier_recovery=carr_rec, mapper=mapper,
                                   samples=samples, filt=filt, exp_ret=exp_ret)

    def test_s25_odd_binary_len_leading_one(self):
        """Odd length input binary expects zero padding: leading 1.

        The resulting demodulated binary will always be even.
        """
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = None       # Defaults to QPSK_MAP
        # QPSK().demodulate() input
        bits = b'1' + generate_bin_bytes(num_bits=254)  # len(bits) == 255
        filt = MatchedFilter.NONE
        # Test case setup
        exp_ret = bits + b'0'  # QPSK output is always even
        samples = create_test_input(sample_rate=samp_rate, symbol_rate=sym_rate,
                                    bin_bytes=bits, bit_map=mapper)
        self.run_test_return_input(sample_rate=samp_rate, symbol_rate=sym_rate,
                                   carrier_recovery=carr_rec, mapper=mapper,
                                   samples=samples, filt=filt, exp_ret=exp_ret)


def create_noisy_test_input(sample_rate: int | float, symbol_rate: int | float,
                            bin_bytes: bytes, snr_db: float | int,
                            bit_map: dict[int, complex] | None = None) -> numpy.ndarray:
    """Transform a binary bytes object into valid test case input that contains AWGN.

    Args:
        sample_rate: The sample rate to modulate bin_bytes with.
        symbol_rate: The symbol rate to modulate bin_bytes with.
        bin_bytes: The binary data to modulate.
        snr_db: The desired signal-to-noise ratio, in decibels.
        bit_map: [OPTIONAL] The bit --> complex sample decisions for use with the modulation.
            If None, uses QPSK_MAP (see: gallant_input.modem.constants).
    """
    mapping = bit_map
    if mapping is None:
        mapping = QPSK_MAP
    samples = create_test_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                bin_bytes=bin_bytes, bit_map=mapping)
    return add_awgn(samples=samples, snr_db=snr_db)


def create_test_input(sample_rate: int | float, symbol_rate: int | float,
                      bin_bytes: bytes, bit_map: dict[int, complex] | None = None) -> numpy.ndarray:
    """Transform a binary bytes object into valid test case input.

    Args:
        sample_rate: The sample rate to modulate bin_bytes with.
        symbol_rate: The symbol rate to modulate bin_bytes with.
        bin_bytes: The binary data to modulate.
        bit_map: [OPTIONAL] The bit --> complex sample decisions for use with the modulation.
            If None, uses QPSK_MAP (see: gallant_input.modem.constants).
    """
    mapping = bit_map
    if mapping is None:
        mapping = QPSK_MAP
    return convert_bin_bytes_to_qpsk(bin_bytes=bin_bytes, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate, bit_map=mapping)


if __name__ == '__main__':
    execute_test_cases()
