"""Defines the base GAIN unit test class.

BaseUnitTest is the parent class for all GAIN related unit test classe inheritance.
It was created at the test-package level because some of the component testing made more sense
to use TediousUnitTest as a parent class.  As such, this class exists to share functionality
between the test.unit_test and test.comp_test sub-packages.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.base_unit_test import BaseUnitTest

    class GainUnitTest(BaseUnitTest):

        # Child class must override this method
        def call_callable(self):
            return my_function(*self._args, **self._kwargs)

        # Child class must override this method
        def validate_return_value(self):
            self._validate_return_value(return_value=return_value)

        # This is your test case
        def test_stuff(self):
            self.set_test_input(1, 2)
            self.expect_return(3)
"""

# Standard Imports
from pathlib import Path
from typing import Any, Tuple
# Third Party Imports
from tediousstart.tediousunittest import TediousUnitTest
from numpy.typing import DTypeLike
import numpy
# Local Imports
from gallant_input.constants import SIG_GLOB_DESCRIPTION_KEY
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from test import REPO_TL_DIR


# pylint: disable=too-many-instance-attributes
class BaseUnitTest(TediousUnitTest):
    """Parent class for all GAIN related unit tests.

    Inherit from this class, define necessary functionality for the function you're testing and
    be sure to override the following methods in your child class:
        call_callable()
        validate_return_value()

    Available features:
        See: help(TediousUnitTest)
    """

    # SNR defaults (dB)
    SNR_VERY_POOR = -0.1
    SNR_POOR = 5.0
    SNR_MARGINAL = 15.0
    SNR_GOOD = 25.0
    SNR_VERY_GOOD = 35.0
    SNR_EXCELLENT = 40.0

    # array([0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j, 0.+0.j], dtype=complex64)
    SAMPLES_OOK_ALL_ZEROES = numpy.zeros(8, dtype=numpy.complex64)
    # array([1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j], dtype=complex64)
    SAMPLES_OOK_ALL_ONES = numpy.ones(8, dtype=numpy.complex64)
    # array([1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j], dtype=complex64)
    SAMPLES_OOK_ALL_10S = numpy.resize([1, 0], 8).astype(numpy.complex64)
    # array([0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j], dtype=complex64)
    SAMPLES_OOK_ALL_01S = numpy.resize([0, 1], 8).astype(numpy.complex64)

    # REALISTIC BINARY DATA
    DEMOD_101_FOI_1_PREAMBLE = b'010101010101010101010101010101011101001110010001'
    # Welcome back! This is Demod 101 part 2. flag{fr3quEnCy_sH1F7_k3y}
    DEMOD_101_FOI_1_PDU = \
        b'0101011101100101011011000110001101101111011011010110010100100000' \
        b'0110001001100001011000110110101100100001001000000101010001101000' \
        b'0110100101110011001000000110100101110011001000000100010001100101' \
        b'0110110101101111011001000010000000110001001100000011000100100000' \
        b'0111000001100001011100100111010000100000001100100010111000100000' \
        b'0110011001101100011000010110011101111011011001100111001000110011' \
        b'0111000101110101010001010110111001000011011110010101111101110011' \
        b'0100100000110001010001100011011101011111011010110011001101111001' \
        b'01111101'
    DEMOD_101_FOI_2_PREAMBLE = b'010101010101010101010101010101011101001110010001'
    DEMOD_101_FOI_3_PREAMBLE = b'010101010101010101010101010101011101001110010001'

    # RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO    "
    RDS_SET1_GRP01_MSG00_OFF00 = \
        b'0011011001011000100001101100000000111011001101011000' \
        b'1110000110001000111110011001001011010011111111001100'  # "KO"
    RDS_SET1_GRP02_MSG00_OFF01 = \
        b'0011011001011000100001101100000000111010010110111100' \
        b'1110000110001000111110011001001110010011110001100000'  # "NO"
    RDS_SET1_GRP03_MSG00_OFF02 = \
        b'0011011001011000100001101100000000111010101101110111' \
        b'1110000110001000111110011000100000001000000011011100'  # "  "
    RDS_SET1_GRP04_MSG00_OFF03 = \
        b'0011011001011000100001101100000000111011110110010011' \
        b'1110000110001000111110011000100000001000000011011100'  # "  "
    # RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO    "
    RDS_SET1_MSG00A = RDS_SET1_GRP01_MSG00_OFF00 + RDS_SET1_GRP02_MSG00_OFF01 \
        + RDS_SET1_GRP03_MSG00_OFF02 + RDS_SET1_GRP04_MSG00_OFF03

    FHSS_CHANNEL_01_PREAMBLE = b'1100110101010101010011001101010101010100'  # RF JQR 5.05 FHSS

    RDS_BLOCK_A3 = bytes('01010111000111010101011100', 'utf-8')             # RF JQR 5.03 RDS group
    RDS_BLOCK_B3 = bytes('00100001001001011011001000', 'utf-8')             # RF JQR 5.03 RDS group
    RDS_BLOCK_C3 = bytes('11001101110011011010110011', 'utf-8')             # RF JQR 5.03 RDS group
    RDS_BLOCK_D3 = bytes('01000110010011010001001011', 'utf-8')             # RF JQR 5.03 RDS group
    RDS_GROUP1 = RDS_BLOCK_A3 + RDS_BLOCK_B3 + RDS_BLOCK_C3 + RDS_BLOCK_D3  # RF JQR 5.03 RDS

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """BaseUnitTest ctor."""
        # ATTRIBUTES
        self.input_sample_rate = None
        self.input_symbol_rate = None
        # File-based test input
        self.test_input_dir = REPO_TL_DIR / 'test' / 'test_input'  # Dir for input files
        self.test_bfsk_in1 = self.test_input_dir / 'bfsk_mod1_c0hz_s48000_b80.sigmf-data'
        self.test_bfsk_in2 = self.test_input_dir / 'bfsk_mod2_c0hz_s57000_b2375.sigmf-data'
        self.test_bfsk_in3 = self.test_input_dir / 'bfsk_mod3_c0hz_s480000_b800.sigmf-data'
        # Demod 101 FoI 3 filtered and decimated
        self.test_bfsk_in4 = self.test_input_dir / 'bfsk_mod4_c0hz_s240k_b600.sigmf-data'
        # Demod 101 FoI 1 filtered and decimated
        self.test_bpsk_in1 = self.test_input_dir / 'bpsk_mod1_c0hz_s4800_b1200.sigmf-data'
        # really-distinct-signal RDS signal exported from GRC
        self.test_bpsk_in2 = self.test_input_dir / 'bpsk_mod2_c0hz_s19k_b1187p5.sigmf-data'

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # return the_function_you_are_testing(*self._args, **self._kwargs)
        raise NotImplementedError(
            self._test_error.format('The child class must override the call_callable method with '
                                    'the function to test.'))

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call.

        Child class must override this method.
        See TediousUnitTest.validate_return_value() for details.
        """
        # Example Usage:
        # self._validate_return_value(return_value=return_value)
        raise NotImplementedError(
            self._test_error.format('The child class must override the validate_return_value '
                                    'method with the appropriate validation logic'))

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def get_test_file_input(self, file_input: Path, sample_dtype: DTypeLike = numpy.complex64,
                            sigmf_data: bool = True) -> Tuple[numpy.ndarray, bytes]:
        """Read a SigMF file to use as file-based test case input.

        Utilizes GAIN.io.read_samples() to read file_input to get samples and, if file_input
        is a SigMF file format, the SigMF global descriptions (which should include the expected
        demodulate return value).

        Args:
            file_input: The file to read samples (and maybe a description) from.
            sample_dtype: [OPTIONAL] The samples data type.
            sigmf_data: [OPTIONAL] If True, read file_input as a SigMF file.

        Returns:
            A tuple of the samples and the description (as a bytes object).  The description
            will be None if sigmf_data is False (because there's no metadata to read from).
        """
        # LOCAL VARIABLES
        samples = None      # ndarray read from file_input
        description = None  # Description string, converted to bytes, parsed from SigMF metadata

        # VALIDATION
        self._validate_type(file_input, 'file_input', Path)
        self._validate_file(str(file_input.absolute()), 'file_input', must_exist=True)
        self._validate_type(sigmf_data, 'sigmf_data', bool)
        # sample_dtype will be validated by subsequent calls to GAIN

        # GET IT
        # Samples
        try:
            samples = read_samples(filename=file_input, sample_dtype=sample_dtype,
                                   sigmf_data=sigmf_data)
        except (OSError, TypeError, ValueError) as err:
            self.fail_test_case(repr(err))
        # Description
        try:
            if sigmf_data is True:
                tmp_obj = SigMFMetaParser(meta_filename=file_input)
                description = tmp_obj.get_global_key(key=SIG_GLOB_DESCRIPTION_KEY)
                if not description:
                    self.fail_test_case('The description (AKA expected result) is missing from '
                                        f'{str(file_input.absolute())}')
                description = bytes(description, 'ascii')
        except (FileNotFoundError, KeyError, TypeError, ValueError) as err:
            self.fail_test_case(repr(err))

        # DONE
        return tuple((samples, description))

    def set_modem_ctor_args(self, sample_rate: Any, symbol_rate: Any) -> None:
        """Sets the Modem() argument values in the test class."""
        self.input_sample_rate = sample_rate
        self.input_symbol_rate = symbol_rate

    def validate_bin_bytes_return_value(self, return_value: bytes):
        """Defines how the class will validate bin_bytes return values of the tested call."""
        self._validate_return_value(return_value=return_value)  # At least there's a SPOT now...

    def validate_ndarray_return_type(self, return_value: numpy.ndarray) -> bool:
        """Completely validate numpy.ndarray return values of the tested call.

        Tests type.

        Returns:
            True if valid, False otherwise.
        """
        # LOCAL VARIABLES
        valid = True

        # VALIDATE IT
        # Type
        if not isinstance(return_value, type(self._exp_return)):
            self._add_test_failure(f'Expected type {type(self._exp_return)} '
                                   f'but it was of type {type(return_value)}')
            valid = False

        # DONE
        return valid

    def validate_ndarray_return_value(self, return_value: numpy.ndarray):
        """Completely validate numpy.ndarray return values of the tested call.

        Tests type, number of dimensions, shape, data type, and all values.
        """
        # LOCAL VARIABLES
        def_error = 'Array {} mismatch:'  # Default error string template
        dtype = None                      # Expected return data type

        # VALIDATE IT
        # Type
        if self.validate_ndarray_return_type(return_value=return_value):
            dtype = self._exp_return.dtype
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
            if return_value.dtype != dtype:
                self._add_test_failure(f'{def_error.format("dtype")} Expected '
                                       f'{dtype} shape '
                                       f'but received {return_value.dtype} instead')
            # Final Catch All
            # Floating point type arrays require special comparison
            if numpy.issubdtype(dtype, numpy.floating) \
                    or numpy.issubdtype(dtype, numpy.complexfloating):
                if not numpy.allclose(return_value, self._exp_return, atol=1e-6, rtol=0):
                    self._add_test_failure(f'The expected {dtype} array is not equivalent '
                                           'to the returned array')
            # Non-floating point comparison
            elif not numpy.array_equal(return_value, self._exp_return):
                self._add_test_failure('The expected array is not equal to the returned array')

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

# pylint: enable=too-many-instance-attributes
