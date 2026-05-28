"""Unit test module for SigMFDTypeInfo.read_dtype.

Typical Usage:
    python -m test                                      # Run *all* the test cases
    python -m test.unit_test                            # Run *all* the unit test cases
    python -m test.unit_test.test_sigmf                 # Run *all* ais sub-package test cases
    python -m test.unit_test.test_sigmf.test_dtypeinfo  # Run *all* SigMFDTypeInfo method tests
    # Run just these unit tests
    python -m test.unit_test.test_sigmf.test_dtypeinfo.test_dtypeinfo_read_dtype
    # Run just this normal 1 unit test
    python -m test.unit_test.test_sigmf.test_dtypeinfo.test_dtypeinfo_read_dtype -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from test.unit_test.test_sigmf.test_dtypeinfo import SigMFDTypeInfoUnitTest


# Calm down, Pylint.  They're just test cases!
# pylint: disable=too-many-public-methods
class SigMFDTypeInfoGetDTypeUnitTest(SigMFDTypeInfoUnitTest):
    """Parent class for all SigMFDTypeInfo.read_dtype unit tests.

    Attributes:
        input_ap_bin_bytes:  # Test case input: AISPayload(bin_bytes)
        test_case_data:      # Stores data about the test case as a TestCaseData object
        test_input_dir:      # Default input directory (OPTIONAL)
        test_output_dir:     # Default output directory (OPTIONAL)
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        test_obj = self.create_test_obj()
        return test_obj.read_dtype

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input() before calling this method.

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_input_exception(self, test_input: Any, exception_type: Exception,
                                 exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            test_input: The SigMFDTypeInfo() argument.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(test_input)
        self.run_test_exception(exception_type=exception_type, exception_msg=exception_msg)

    def run_test_input_return(self, test_input: str, exp_return: type | str) -> None:
        """Common method calls for a test case expected to return.

        Args:
            test_input: Well-formed string to use as the SigMFDTypeInfo() argument.
            exp_return: The expected value of SigMFDTypeInfo.read_dtype, as a data type or
                dataset string (e.g., '>c8'), normalized as a numpy.dtype object.
        """
        self.set_test_input(test_input)
        self.run_test_return(exp_return=numpy.dtype(exp_return))

    def run_test_return(self, exp_return: type | str) -> None:
        """Common method calls for a test case expected to return.

        Test author must set test input before caling this method.

        Args:
            exp_return: The expected value of SigMFDTypeInfo.read_dtype.
        """
        self.expect_return(exp_return)
        self.run_test()


class NormalSigMFDTypeInfoGetDTypeUnitTest(SigMFDTypeInfoGetDTypeUnitTest):
    """Normal Test Cases."""

    def test_n01_complex_float_cf32_le(self):
        """Valid SigMF Dataset Format (complex float): cf32_le."""
        exp_return = numpy.complex64
        test_input = 'cf32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n02_complex_float_cf32_be(self):
        """Valid SigMF Dataset Format (complex float): cf32_be."""
        exp_return = '>c8'
        test_input = 'cf32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n03_complex_float_cf64_le(self):
        """Valid SigMF Dataset Format (complex float): cf64_le."""
        exp_return = numpy.complex128
        test_input = 'cf64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n04_complex_float_cf64_be(self):
        """Valid SigMF Dataset Format (complex float): cf64_be."""
        exp_return = '>c16'
        test_input = 'cf64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n05_real_float_rf32_le(self):
        """Valid SigMF Dataset Format (real float): rf32_le."""
        exp_return = numpy.float32
        test_input = 'rf32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n06_real_float_rf32_be(self):
        """Valid SigMF Dataset Format (real float): rf32_be."""
        exp_return = '>f4'
        test_input = 'rf32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n07_real_float_rf64_le(self):
        """Valid SigMF Dataset Format (real float): rf64_le."""
        exp_return = numpy.float64
        test_input = 'rf64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n08_real_float_rf64_be(self):
        """Valid SigMF Dataset Format (real float): rf64_be."""
        exp_return = '>f8'
        test_input = 'rf64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n09_complex_signed_int_ci32_le(self):
        """Valid SigMF Dataset Format (complex signed_int): ci32_le."""
        exp_return = numpy.int32
        test_input = 'ci32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n10_complex_signed_int_ci32_be(self):
        """Valid SigMF Dataset Format (complex signed_int): ci32_be."""
        exp_return = numpy.dtype('>i4')
        test_input = 'ci32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n11_complex_signed_int_ci16_le(self):
        """Valid SigMF Dataset Format (complex signed_int): ci16_le."""
        exp_return = numpy.int16
        test_input = 'ci16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n12_complex_signed_int_ci16_be(self):
        """Valid SigMF Dataset Format (complex signed_int): ci16_be."""
        exp_return = numpy.dtype('>i2')
        test_input = 'ci16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n13_real_signed_int_ri32_le(self):
        """Valid SigMF Dataset Format (real signed_int): ri32_le."""
        exp_return = numpy.int32
        test_input = 'ri32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n14_real_signed_int_ri32_be(self):
        """Valid SigMF Dataset Format (real signed_int): ri32_be."""
        exp_return = numpy.dtype('>i4')  # big-endian signed int 4 bytes
        test_input = 'ri32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n15_real_signed_int_ri16_le(self):
        """Valid SigMF Dataset Format (real signed_int): ri16_le."""
        exp_return = numpy.int16
        test_input = 'ri16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n16_real_signed_int_ri16_be(self):
        """Valid SigMF Dataset Format (real signed_int): ri16_be."""
        exp_return = numpy.dtype('>i2')  # big-endian signed int 2 bytes
        test_input = 'ri16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n17_complex_unsigned_int_cu32_le(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu32_le."""
        exp_return = numpy.uint32
        test_input = 'cu32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n18_complex_unsigned_int_cu32_be(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu32_be."""
        exp_return = numpy.dtype('>u4')
        test_input = 'cu32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n19_complex_unsigned_int_cu16_le(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu16_le."""
        exp_return = numpy.uint16
        test_input = 'cu16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n20_complex_unsigned_int_cu16_be(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu16_be."""
        exp_return = numpy.dtype('>u2')
        test_input = 'cu16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n21_real_unsigned_int_ru32_le(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru32_le."""
        exp_return = numpy.uint32
        test_input = 'ru32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n22_real_unsigned_int_ru32_be(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru32_be."""
        exp_return = numpy.dtype('>u4')  # big-endian unsigned int 4 bytes
        test_input = 'ru32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n23_real_unsigned_int_ru16_le(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru16_le."""
        exp_return = numpy.uint16
        test_input = 'ru16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n24_real_unsigned_int_ru16_be(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru16_be."""
        exp_return = numpy.dtype('>u2')  # big-endian unsigned int 2 bytes
        test_input = 'ru16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n25_complex_signed_int_ci8(self):
        """Valid SigMF Dataset Format (complex signed_int): ci8."""
        exp_return = numpy.int8
        test_input = 'ci8'
        self.run_test_input_return(test_input, exp_return)

    def test_n26_complex_unsigned_int_cu8(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu8."""
        exp_return = numpy.uint8
        test_input = 'cu8'
        self.run_test_input_return(test_input, exp_return)

    def test_n27_real_signed_int_ri8(self):
        """Valid SigMF Dataset Format (real signed_int): ri8."""
        exp_return = numpy.int8
        test_input = 'ri8'
        self.run_test_input_return(test_input, exp_return)

    def test_n28_real_unsigned_int_ru8(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru8."""
        exp_return = numpy.uint8
        test_input = 'ru8'
        self.run_test_input_return(test_input, exp_return)


class ErrorSigMFDTypeInfoGetDTypeUnitTest(SigMFDTypeInfoGetDTypeUnitTest):
    """Error Test Cases."""

    def test_e01_bad_type_bytes(self):
        """Bad ctor 'dataset' data type input: bytes data type."""
        test_input = b'cf32_le'
        exp_except = TypeError
        exp_except_msg = 'argument should have been of type '
        self.run_test_input_exception(test_input, exp_except, exp_except_msg)

    def test_e02_bad_type_none(self):
        """Bad ctor 'dataset' data type input: None."""
        test_input = None
        exp_except = TypeError
        exp_except_msg = 'argument should have been of type '
        self.run_test_input_exception(test_input, exp_except, exp_except_msg)

    def test_e03_bad_value_empty(self):
        """Bad ctor 'dataset' input value: empty string."""
        test_input = ''
        exp_except = ValueError
        exp_except_msg = 'argument can not be empty'
        self.run_test_input_exception(test_input, exp_except, exp_except_msg)

    def test_e04_invalid_format(self):
        """Bad ctor 'dataset' input value: gibberish string."""
        test_input = 'why does this library parse strings?!'
        exp_except = RuntimeError
        exp_except_msg = 'failed SigMF validation with a bespoke Exception'
        self.run_test_input_exception(test_input, exp_except, exp_except_msg)


# pylint: enable=too-many-public-methods


if __name__ == '__main__':
    execute_test_cases()
