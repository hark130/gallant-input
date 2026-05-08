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
from typing import Any
# Third Party Imports
from tediousstart.tediousunittest import TediousUnitTest
import numpy
# Local Imports


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
    SAMPLES_ALL_ZEROES = numpy.zeros(8, dtype=numpy.complex64)
    # array([1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j, 1.+0.j], dtype=complex64)
    SAMPLES_ALL_ONES = numpy.ones(8, dtype=numpy.complex64)
    # array([1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j], dtype=complex64)
    SAMPLES_ALL_10S = numpy.resize([1, 0], 8).astype(numpy.complex64)
    # array([0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j], dtype=complex64)
    SAMPLES_ALL_01S = numpy.resize([0, 1], 8).astype(numpy.complex64)

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

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """BaseUnitTest ctor."""
        # ATTRIBUTES
        self.input_sample_rate = None
        self.input_symbol_rate = None

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

    def set_modem_ctor_args(self, sample_rate: Any, symbol_rate: Any) -> None:
        """Sets the Modem() argument values in the test class."""
        self.input_sample_rate = sample_rate
        self.input_symbol_rate = symbol_rate

    def validate_bin_bytes_return_value(self, return_value: bytes):
        """Defines how the class will validate bin_bytes return values of the tested call."""
        self._validate_return_value(return_value=return_value)  # At least there's a SPOT now...

    def validate_ndarray_return_value(self, return_value: numpy.ndarray):
        """Defines how the class will validate numpy.ndarray return values of the tested call."""
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

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
