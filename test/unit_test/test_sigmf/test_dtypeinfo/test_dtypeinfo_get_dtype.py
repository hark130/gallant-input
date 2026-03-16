"""Unit test module for SigMFDTypeInfo.get_dtype.

Typical Usage:
    python -m test                                      # Run *all* the test cases
    python -m test.unit_test                            # Run *all* the unit test cases
    python -m test.unit_test.test_sigmf                 # Run *all* ais sub-package test cases
    python -m test.unit_test.test_sigmf.test_dtypeinfo  # Run *all* SigMFDTypeInfo method tests
    # Run just these unit tests
    python -m test.unit_test.test_sigmf.test_dtypeinfo.test_dtypeinfo_get_dtype
    # Run just this normal 1 unit test
    python -m test.unit_test.test_sigmf.test_dtypeinfo.test_dtypeinfo_get_dtype -k n01
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
    """Parent class for all SigMFDTypeInfo.get_dtype unit tests.

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
        return test_obj.get_dtype

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

    def run_test_input_return(self, test_input: bytes, exp_return: type) -> None:
        """Common method calls for a test case expected to return.

        Args:
            test_input: Well-formed string to use as the SigMFDTypeInfo() argument.
            exp_return: The expected value of SigMFDTypeInfo.get_dtype, normalized as a
                numpy.dtype object.
        """
        self.set_test_input(test_input)
        self.run_test_return(exp_return=numpy.dtype(exp_return))

    def run_test_return(self, exp_return: int) -> None:
        """Common method calls for a test case expected to return.

        Test author must set test input before caling this method.

        Args:
            exp_return: The expected value of SigMFDTypeInfo.get_dtype.
        """
        self.expect_return(exp_return)
        self.run_test()


class NormalSigMFDTypeInfoGetDTypeUnitTest(SigMFDTypeInfoGetDTypeUnitTest):
    """Normal Test Cases."""

    def test_n01_complex_float_cf32_le(self):
        """Valid SigMF Dataset Format (complex float): cf32_le."""
        exp_return = numpy.float32
        test_input = f'cf32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n02_complex_float_cf32_be(self):
        """Valid SigMF Dataset Format (complex float): cf32_be."""
        exp_return = numpy.dtype('>f4')  # big-endian floating-point 4 bytes
        test_input = f'cf32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n03_complex_float_cf64_le(self):
        """Valid SigMF Dataset Format (complex float): cf64_le."""
        exp_return = numpy.float64
        test_input = f'cf64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n04_complex_float_cf64_be(self):
        """Valid SigMF Dataset Format (complex float): cf64_be."""
        exp_return = numpy.dtype('>f8')  # big-endian floating-point 8 bytes
        test_input = f'cf64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n05_real_float_rf32_le(self):
        """Valid SigMF Dataset Format (real float): rf32_le."""
        exp_return = numpy.float32
        test_input = f'rf32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n06_real_float_rf32_be(self):
        """Valid SigMF Dataset Format (real float): rf32_be."""
        exp_return = numpy.dtype('>f4')  # big-endian floating-point 4 bytes
        test_input = f'rf32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n07_real_float_rf64_le(self):
        """Valid SigMF Dataset Format (real float): rf64_le."""
        exp_return = numpy.dtype('<f8')  # big-endian floating-point 8 bytes
        test_input = f'rf64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n08_real_float_rf64_be(self):
        """Valid SigMF Dataset Format (real float): rf64_be."""
        exp_return = numpy.dtype('>f8')  # big-endian floating-point 8 bytes
        test_input = f'rf64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n09_complex_signed_int_ci32_le(self):
        """Valid SigMF Dataset Format (complex signed_int): ci32_le."""
        exp_return = numpy.int32
        test_input = f'ci32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n10_complex_signed_int_ci32_be(self):
        """Valid SigMF Dataset Format (complex signed_int): ci32_be."""
        exp_return = numpy.dtype('>i4')  # big-endian signed int 4 bytes
        test_input = f'ci32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n11_complex_signed_int_ci16_le(self):
        """Valid SigMF Dataset Format (complex signed_int): ci16_le."""
        exp_return = numpy.int16
        test_input = f'ci16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n12_complex_signed_int_ci16_be(self):
        """Valid SigMF Dataset Format (complex signed_int): ci16_be."""
        exp_return = numpy.dtype('>i2')  # big-endian signed int 2 bytes
        test_input = f'ci16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n13_real_signed_int_ri32_le(self):
        """Valid SigMF Dataset Format (real signed_int): ri32_le."""
        exp_return = numpy.int32
        test_input = f'ri32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n14_real_signed_int_ri32_be(self):
        """Valid SigMF Dataset Format (real signed_int): ri32_be."""
        exp_return = numpy.dtype('>i4')  # big-endian signed int 4 bytes
        test_input = f'ri32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n15_real_signed_int_ri16_le(self):
        """Valid SigMF Dataset Format (real signed_int): ri16_le."""
        exp_return = numpy.int16
        test_input = f'ri16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n16_real_signed_int_ri16_be(self):
        """Valid SigMF Dataset Format (real signed_int): ri16_be."""
        exp_return = numpy.dtype('>i2')  # big-endian signed int 2 bytes
        test_input = f'ri16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n17_complex_unsigned_int_cu32_le(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu32_le."""
        exp_return = numpy.uint32
        test_input = f'cu32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n18_complex_unsigned_int_cu32_be(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu32_be."""
        exp_return = numpy.dtype('>u4')  # big-endian unsigned int 4 bytes
        test_input = f'cu32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n19_complex_unsigned_int_cu16_le(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu16_le."""
        exp_return = numpy.uint16
        test_input = f'cu16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n20_complex_unsigned_int_cu16_be(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu16_be."""
        exp_return = numpy.dtype('>u2')  # big-endian unsigned int 2 bytes
        test_input = f'cu16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n21_real_unsigned_int_ru32_le(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru32_le."""
        exp_return = numpy.uint32
        test_input = f'ru32_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n22_real_unsigned_int_ru32_be(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru32_be."""
        exp_return = numpy.dtype('>u4')  # big-endian unsigned int 4 bytes
        test_input = f'ru32_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n23_real_unsigned_int_ru16_le(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru16_le."""
        exp_return = numpy.uint16
        test_input = f'ru16_le'
        self.run_test_input_return(test_input, exp_return)

    def test_n24_real_unsigned_int_ru16_be(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru16_be."""
        exp_return = numpy.dtype('>u2')  # big-endian unsigned int 2 bytes
        test_input = f'ru16_be'
        self.run_test_input_return(test_input, exp_return)

    def test_n25_complex_signed_int_ci8(self):
        """Valid SigMF Dataset Format (complex signed_int): ci8."""
        exp_return = numpy.int8
        test_input = f'ci8'
        self.run_test_input_return(test_input, exp_return)

    def test_n26_complex_unsigned_int_cu8(self):
        """Valid SigMF Dataset Format (complex unsigned_int): cu8."""
        exp_return = numpy.uint8
        test_input = f'cu8'
        self.run_test_input_return(test_input, exp_return)

    def test_n27_real_signed_int_ri8(self):
        """Valid SigMF Dataset Format (real signed_int): ri8."""
        exp_return = numpy.int8
        test_input = f'ri8'
        self.run_test_input_return(test_input, exp_return)

    def test_n28_real_unsigned_int_ru8(self):
        """Valid SigMF Dataset Format (real unsigned_int): ru8."""
        exp_return = numpy.uint8
        test_input = f'ru8'
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


class SpecialSigMFDTypeInfoGetDTypeUnitTest(SigMFDTypeInfoGetDTypeUnitTest):
    """Special Test Cases."""

    def test_s01_complex_signed_int_ci64_le(self):
        """Valid (yet uncommon?) SigMF Dataset Format (complex signed_int): ci64_le."""
        exp_return = numpy.int64
        test_input = f'ci64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_s02_complex_signed_int_ci64_be(self):
        """Valid (yet uncommon?) SigMF Dataset Format (complex signed_int): ci64_be."""
        exp_return = numpy.dtype('>i8')  # big-endian signed int 8 bytes
        test_input = f'ci64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_s03_real_signed_int_ri64_le(self):
        """Valid (yet uncommon?) SigMF Dataset Format (real signed_int): ri64_le."""
        exp_return = numpy.int64
        test_input = f'ri64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_s04_real_signed_int_ri64_be(self):
        """Valid (yet uncommon?) SigMF Dataset Format (real signed_int): ri64_be."""
        exp_return = numpy.dtype('>i8')  # big-endian signed int 8 bytes
        test_input = f'ri64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_s05_complex_unsigned_int_cu64_le(self):
        """Valid (yet uncommon?) SigMF Dataset Format (complex unsigned_int): cu64_le."""
        exp_return = numpy.uint64
        test_input = f'cu64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_s06_complex_unsigned_int_cu64_be(self):
        """Valid (yet uncommon?) SigMF Dataset Format (complex unsigned_int): cu64_be."""
        exp_return = numpy.dtype('>u8')  # big-endian unsigned int 8 bytes
        test_input = f'cu64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_s07_real_unsigned_int_ru64_le(self):
        """Valid (yet uncommon?) SigMF Dataset Format (real unsigned_int): ru64_le."""
        exp_return = numpy.uint64
        test_input = f'ru64_le'
        self.run_test_input_return(test_input, exp_return)

    def test_s08_real_unsigned_int_ru64_be(self):
        """Valid (yet uncommon?) SigMF Dataset Format (real unsigned_int): ru64_be."""
        exp_return = numpy.dtype('>u8')  # big-endian unsigned int 8 bytes
        test_input = f'ru64_be'
        self.run_test_input_return(test_input, exp_return)

    def test_s09_complex_signed_int_ci8_superfluous_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (complex signed_int w/ endianness): ci8_le."""
        exp_return = numpy.int8
        test_input = f'ci8_le'
        self.run_test_input_return(test_input, exp_return)

    def test_s10_complex_unsigned_int_cu8_superfluous_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (complex unsigned_int w/ endianness): cu8_be."""
        exp_return = numpy.uint8
        test_input = f'cu8_be'
        self.run_test_input_return(test_input, exp_return)

    def test_s11_real_signed_int_ri8_superfluous_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (real signed_int w/ endianness): ri8_le."""
        exp_return = numpy.int8
        test_input = f'ri8_le'
        self.run_test_input_return(test_input, exp_return)

    def test_s12_real_unsigned_int_ru8_superfluous_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (real unsigned_int w/ endianness): ru8_be."""
        exp_return = numpy.uint8
        test_input = f'ru8_be'
        self.run_test_input_return(test_input, exp_return)

    def test_s13_complex_signed_int_ci64_without_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (complex signed_int w/out endianness): ci64."""
        exp_return = numpy.int64
        test_input = f'ci64'
        self.run_test_input_return(test_input, exp_return)

    def test_s14_complex_unsigned_int_cu64_without_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (complex unsigned_int w/out endianness): cu64."""
        exp_return = numpy.uint64
        test_input = f'cu64'
        self.run_test_input_return(test_input, exp_return)

    def test_s15_real_signed_int_ri64_without_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (real signed_int w/out endianness): ri64."""
        exp_return = numpy.int64
        test_input = f'ri64'
        self.run_test_input_return(test_input, exp_return)

    def test_s16_real_unsigned_int_ru64_without_endianness(self):
        """Valid (uncommon?) SigMF Dataset Format (real unsigned_int w/out endianness): ru64."""
        exp_return = numpy.uint64
        test_input = f'ru64'
        self.run_test_input_return(test_input, exp_return)

    def test_s17_text_parsing_cf32_le(self):
        """Undocumented(?!) string parsing: cf32_le."""
        exp_return = numpy.float32
        test_input = f'complex floating-point 32 little-endian'  # cf32_le
        self.run_test_input_return(test_input, exp_return)

    def test_s18_text_parsing_ri16_be(self):
        """Undocumented(?!) string parsing: ri16_be.

        Apparently, sigmffile.dtype_info() can parse strings if you use the right keywords!.
        """
        exp_return = numpy.int16
        test_input = f'real signed-integer 16 big-endian'  # ri16_be
        self.run_test_input_return(test_input, exp_return)

    def test_s19_text_parsing_u8(self):
        """Undocumented(?!) string parsing: u8."""
        exp_return = numpy.uint8
        test_input = f'unsigned-integer 8'  # u8
        self.run_test_input_return(test_input, exp_return)
# pylint: enable=too-many-public-methods


if __name__ == '__main__':
    execute_test_cases()
