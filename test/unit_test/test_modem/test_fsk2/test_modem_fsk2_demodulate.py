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
from gallant_input.io import read_samples
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
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
        self.test_input_dir = REPO_TL_DIR / 'test' / 'test_input'  # Dir for input files
        # File-based test input

        self.test_in1 = self.test_input_dir / 'bfsk_mod1_c0hz_s48000_b80.sigmf-data'
        self.test_in2 = self.test_input_dir / 'bfsk_mod2_c0hz_s57000_b2375.sigmf-data'
        self.test_in3 = self.test_input_dir / 'bfsk_mod3_c0hz_s480000_b800.sigmf-data'

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.demodulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self.validate_bin_bytes_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def get_test_file_input(self, sigmf_input: Path, sample_dtype: DTypeLike = numpy.complex64
                            ) -> Tuple[numpy.ndarray, bytes]:
        """Read a SigMF file to use as file-based test case input.

        Utilizes GAIN.io.read_samples() to read sigmf_input to get samples and the SigMF global
        descriptions (which should include the expected demodulate return value).

        Args:
            sigmf_input: The file to use.
            sample_dtype: The samples data type.

        Returns:
            A tuple of the samples and the description (as a bytes object).
        """
        # LOCAL VARIABLES
        samples = None  # ndarray read from sigmf_input
        description = b''  # Description string, converted to bytes, parsed from SigMF metadata

        # VALIDATION
        self._validate_type(sigmf_input, 'sigmf_input', Path)
        self._validate_file(str(sigmf_input.absolute()), 'sigmf_input', must_exist=True)
        # sample_dtype will be validated by subsequent calls to GAIN

        # GET IT
        # Samples
        try:
            samples = read_samples(filename=sigmf_input, sample_dtype=sample_dtype, sigmf_data=True)
        except (OSError, TypeError, ValueError) as err:
            self.fail_test_case(repr(err))
        # Description
        try:
            tmp_obj = SigMFMetaParser(meta_filename=sigmf_input)
            description = tmp_obj.get_global_key(key=SIG_GLOB_DESCRIPTION_KEY)
            if not description:
                self.fail_test_case('The description (AKA expected result) is missing from '
                                    f'{str(sigmf_input.absolute())}')
            description = bytes(description, 'ascii')
        except (FileNotFoundError, KeyError, TypeError, ValueError) as err:
            self.fail_test_case(repr(err))

        # DONE
        return tuple((samples, description))

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
        samples, description = self.get_test_file_input(sigmf_input, sample_dtype)
        # Set it
        self.set_test_input(samples)
        self.expect_return(description)  # The "answer" should be in the SigMF metadata

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
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate argument input.  Accepts any input, bad or otherwise.
            symbol_rate: Sets the symbol_rate argument input.  Accepts any input, bad or otherwise.
            samples: Test case input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(samples)
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

    def run_test_return_input(self, sample_rate: float, symbol_rate: float, samples: numpy.ndarray,
                              exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return an expected result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            samples: Test case input.
            threshold: Test case input.
            exp_ret: The expected return value from the method call.
        """
        self.set_test_input(samples)
        self.run_test_return(sample_rate=sample_rate, symbol_rate=symbol_rate, exp_ret=exp_ret)

    def run_test_return_file(self, sample_rate: float, symbol_rate: float,
                             sigmf_input: Path, sample_dtype: DTypeLike = numpy.complex64) -> None:
        """Common method calls for a test expected to return using file-based test input.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            sigmf_input: The file to use as a source of samples and expected result.
            sample_dtype: The samples data type.
        """
        self.set_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.set_test_file_input(sigmf_input=sigmf_input, sample_dtype=sample_dtype)
        self.run_test()


class NormalModemFSK2DemodulateUnitTest(ModemFSK2DemodulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits_sigmf(self):
        """Single byte, alternating bits, parsed from a SigMF input file."""
        samp_rate = 48000
        sym_rate = 80
        self.run_test_return_file(samp_rate, sym_rate, self.test_in1)

    def test_n02_valid_bfsk_sigmf_rds_rates(self):
        """Binary encoded text modulated with 2-FSK from a SigMF input file at RDS rates."""
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        self.run_test_return_file(samp_rate, sym_rate, self.test_in2)

    def test_n03_valid_bfsk_sigmf_demod101_rates(self):
        """Binary encoded text modulated with 2-FSK from a SigMF input file at Demod 101 rates."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        self.run_test_return_file(samp_rate, sym_rate, self.test_in3)

    @skip("TO DO: DON'T DO NOW... Consider adding AWGN to file-based test input")
    def test_n00_single_byte_alt_bits_sigmf_with_awgn(self):
        """Single byte, alternating bits, SigMF input file, with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        self.run_test_return_file(samp_rate, sym_rate, self.test_in1)  # TD:DDN - ADD AWGN

    @skip("TO DO: DON'T DO NOW... Consider adding AWGN to file-based test input")
    def test_n00_valid_bfsk_sigmf_with_awgn(self):
        """Binary encoded text from a SigMF input file, with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        self.run_test_return_file(samp_rate, sym_rate, self.test_in2)  # TD:DDN - ADD AWGN


class ErrorModemFSK2DemodulateUnitTest(ModemFSK2DemodulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        test_in = self.SAMPLES_ALL_ONES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        test_in = self.SAMPLES_ALL_ZEROES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        test_in = self.SAMPLES_ALL_10S
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        test_in = self.SAMPLES_ALL_01S
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        test_in = self.SAMPLES_ALL_ONES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        test_in = self.SAMPLES_ALL_ZEROES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        test_in = self.SAMPLES_ALL_10S
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        test_in = self.SAMPLES_ALL_01S
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        test_in = self.SAMPLES_ALL_ONES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        test_in = self.SAMPLES_ALL_ZEROES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        test_in = self.SAMPLES_ALL_10S
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        test_in = self.SAMPLES_ALL_01S
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_samples_type_none(self):
        """Bad samples: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        test_in = None
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_samples_type_complex_list(self):
        """Bad samples: bad type - list of complex values (almost an ndarray)."""
        samp_rate = 48000
        sym_rate = 800
        test_in = [0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j]
        self.run_test_exception_input(samp_rate, sym_rate, test_in, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_samples_value_empty(self):
        """Bad samples: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        test_in = numpy.array([], dtype=numpy.complex64)  # len(test_in) == 0
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'ndarray may not be empty')

    def test_e16_bad_samples_invalid_dimensions(self):
        """Bad samples: wrong dimensions."""
        samp_rate = 48000
        sym_rate = 800
        test_in = numpy.resize(self.SAMPLES_ALL_10S, (2, 2))  # test_in.ndim == 2
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      f'value is {test_in.ndim}-dimensional instead of '
                                      f'{self.SAMPLES_ALL_10S.ndim}-dimensional')


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
        test_in = self.SAMPLES_ALL_ONES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'argument is not positive')

    def test_b02_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        # Test case input
        test_in = self.SAMPLES_ALL_ZEROES
        self.run_test_exception_input(samp_rate, sym_rate, test_in, ValueError,
                                      'argument is not positive')


if __name__ == '__main__':
    execute_test_cases()
