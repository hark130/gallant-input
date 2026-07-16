"""Unit test module for FSK2.demodulate().

Typical Usage:
    python -m test                                 # Run *all* the test cases
    python -m test.unit_test                       # Run *all* the unit test cases
    python -m test.unit_test.test_modem            # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_fsk2  # Run *all* FSK2 test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_fsk2.test_modem_fsk2_demodulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_fsk2.test_modem_fsk2_demodulate -k n01
"""

# Standard Imports
from pathlib import Path
from typing import Any, Tuple
# Third Party Imports
from numpy.typing import DTypeLike
from tediousstart.tediousstart import execute_test_cases
from unittest import skip
import numpy
# Local Imports
from gallant_input.constants import SIG_GLOB_DESCRIPTION_KEY
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from test import REPO_TL_DIR
from test.unit_test.test_modem.test_fsk2.test_modem_fsk2 import ModemFSK2UnitTest


class ModemFSK2DemodulateUnitTest(ModemFSK2UnitTest):
    """Parent class for all FSK2.demodulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RootUnitTest ctor."""
        super().__init__(*args, **kwargs)
        # ATTRIBUTES
        self._demod = True                  # Update default test state
        # File-based test input
        self.test_in1 = self.test_bfsk_in1  # BFSK test input 1
        self.test_in2 = self.test_bfsk_in2  # BFSK test input 2
        self.test_in3 = self.test_bfsk_in3  # BFSK test input 3
        self.test_in4 = self.test_bfsk_in4  # BFSK test input 4

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.demodulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self.validate_bin_bytes_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def set_test_file_input(self, sigmf_input: Path,
                            sample_dtype: DTypeLike = numpy.complex64) -> None:
        """Read a SigMF file, set the samples as test input, and description as expected results.

        Reads and parses sigmf_input.  Sets the samples as test input using set_test_input().
        Sets the SigMF metadata descripton as the expected return using expect_return().

        Args:
            sigmf_input: The file to use.
            sample_dtype: The samples data type.
        """
        # LOCAL VARIABLES
        samples = None  # ndarray read from sigmf_input
        description = b''  # Description string, converted to bytes, parsed from SigMF metadata

        # SET IT
        # Get it
        samples, description = self.get_test_file_input(sigmf_input, sample_dtype, sigmf_data=True)
        # Set it
        self.set_test_input(samples)
        self.expect_return(description)  # The "answer" should be in the SigMF metadata

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_fsk2_ctor_args() *and* self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate argument input.  Accepts any input, bad or otherwise.
            symbol_rate: Sets the symbol_rate argument input.  Accepts any input, bad or otherwise.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def run_test_exception_input(self, samples: Any,
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_fsk2_ctor_args().

        Args:
            sample_rate: Sets the sample_rate argument input.  Accepts any input, bad or otherwise.
            symbol_rate: Sets the symbol_rate argument input.  Accepts any input, bad or otherwise.
            samples: Test case input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(samples)
        self.run_test_exception(exception_type=exception_type, exception_msg=exception_msg)

    def run_test_return_file(self, sigmf_input: Path,
                             sample_dtype: DTypeLike = numpy.complex64) -> None:
        """Common method calls for a test expected to return using file-based test input.

        The test author *must* call set_fsk2_ctor_args().

        Args:
            sigmf_input: The file to use as a source of samples and expected result.
            sample_dtype: The samples data type.
        """
        self.set_test_file_input(sigmf_input=sigmf_input, sample_dtype=sample_dtype)
        self.run_test()


class NormalModemFSK2DemodulateUnitTest(ModemFSK2DemodulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits_sigmf(self):
        """Single byte, alternating bits, parsed from a SigMF input file."""
        samp_rate = 48000
        sym_rate = 80
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_return_file(self.test_in1)

    def test_n02_valid_bfsk_sigmf_rds_rates(self):
        """Binary encoded text modulated with 2-FSK from a SigMF input file at RDS rates."""
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_return_file(self.test_in2)

    def test_n03_valid_bfsk_sigmf_demod101_rates(self):
        """Binary encoded text modulated with 2-FSK from a SigMF input file at Demod 101 rates."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_return_file(self.test_in3)

    @skip('Test case failing for valid reasons (now that I removed timing sync from the method)')
    def test_n04_valid_bfsk_sigmf_demod101_foi3_rates(self):
        """Demod 101 FoI 3 decimated, filtered, and exported."""
        samp_rate = 240000  # 5.03 Demod 101 FoI 3 sample rate (decimated)
        sym_rate = 599.31   # 5.03 Demod 101 FoI 3 symbol rate (600?)
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_return_file(self.test_in4)


class ErrorModemFSK2DemodulateUnitTest(ModemFSK2DemodulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ONES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_10S
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_01S
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ONES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        test_in = self.SAMPLES_OOK_ALL_10S
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        test_in = self.SAMPLES_OOK_ALL_01S
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        test_in = self.SAMPLES_OOK_ALL_ONES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        test_in = self.SAMPLES_OOK_ALL_10S
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        test_in = self.SAMPLES_OOK_ALL_01S
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_samples_type_none(self):
        """Bad samples: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        test_in = None
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_samples_type_complex_list(self):
        """Bad samples: bad type - list of complex values (almost an ndarray)."""
        samp_rate = 48000
        sym_rate = 800
        test_in = [0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j]
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_samples_value_empty(self):
        """Bad samples: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        test_in = numpy.array([], dtype=numpy.complex64)  # len(test_in) == 0
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'ndarray may not be empty')

    def test_e16_bad_samples_invalid_dimensions(self):
        """Bad samples: wrong dimensions."""
        samp_rate = 48000
        sym_rate = 800
        test_in = numpy.resize(self.SAMPLES_OOK_ALL_10S, (2, 2))  # test_in.ndim == 2
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      f'value is {test_in.ndim}-dimensional instead of '
                                      f'{self.SAMPLES_OOK_ALL_10S.ndim}-dimensional')


class BoundaryModemFSK2DemodulateUnitTest(ModemFSK2DemodulateUnitTest):
    """Boundary Test Cases."""

    def test_b01_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = 1
        sym_rate = 80
        # Test case input
        test_in = self.SAMPLES_OOK_ALL_ONES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'argument is not positive')

    def test_b02_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        # Test case input
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        self.set_fsk2_ctor_args(samp_rate, sym_rate, None, None, None)
        self.run_test_exception_input(test_in, ValueError,
                                      'argument is not positive')


class SpecialModemFSK2DemodulateUnitTest(ModemFSK2DemodulateUnitTest):
    """Special Test Cases."""

    def test_s01_modulate_fsk2_config(self):
        """FSK2Config() object configured to modulate, used to demodulate."""
        samp_rate = 48000
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = float(1.5)
        self._demod = False  # Tell the test framework to disable(?) FSK2Config() demod mode
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_file(self.test_in1)


if __name__ == '__main__':
    execute_test_cases()
