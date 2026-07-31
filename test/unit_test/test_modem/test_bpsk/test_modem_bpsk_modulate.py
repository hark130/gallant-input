"""Unit test module for BPSK.modulate().

Typical Usage:
    python -m test                                 # Run *all* the test cases
    python -m test.unit_test                       # Run *all* the unit test cases
    python -m test.unit_test.test_modem            # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_bpsk  # Run *all* BPSK test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_bpsk.test_modem_bpsk_modulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_bpsk.test_modem_bpsk_modulate -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from gallant_input.modem.constants import BPSK_MAP, QPSK_MAP
from gallant_input.synch.costas_loop import CostasLoop
from test.modify import generate_bin_bytes, rotate_mapping
from test.unit_test.test_modem.test_bpsk.test_modem_bpsk import ModemBPSKUnitTest


class ModemBPSKModulateUnitTest(ModemBPSKUnitTest):
    """Parent class for all BPSK.modulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RootUnitTest ctor."""
        # ATTRIBUTES
        self._exp_ret_ndim = None   # Expected number of dimensions for a valid return value
        self._exp_ret_shape = None  # Expected shape for a valid return value
        self._exp_ret_dtype = None  # Expected dtype for a valid return value

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.modulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self.validate_ndarray_return_details(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call set_bpsk_ctor_args() *and* set_test_input().

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_exception_input(self, bin_bytes: Any, mapper: Any,
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case, with input, expected to raise an exception.

        Test author must call set_bpsk_ctor_args() *and* set_test_input().

        Args:
            bin_bytes: Test case input.
            mapper: Test case input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(bin_bytes, mapper)
        self.run_test_exception(exception_type, exception_msg)

    def run_test_return_def(self) -> None:
        """Common method calls for a test case expected to return with default expected values.

        This method calls set_exp_ret_values() with default values but the test author
        *must* call set_bpsk_ctor_args() *and* set_test_input().
        """
        self.set_exp_ret_values()
        self.run_test()

    def run_test_input_return_def(self, bin_bytes: bytes,
                                  mapper: dict[int, complex] | None) -> None:
        """Common method calls for a test case expected to return with default expected values.

        This method calls set_exp_ret_values() with default values but the test author
        *must* call set_bpsk_ctor_args() *and* set_test_input().

        Args:
            bin_bytes: Test case input.
            mapper: Test case input.
        """
        self.set_test_input(bin_bytes, mapper)
        self.set_exp_ret_values()
        self.run_test()

    def set_exp_ret_values(self, exp_ndim: int | None = 1, exp_shape: int | None = None,
                           exp_dtype: numpy.dtype | None = numpy.complex64) -> None:
        """Set the expect return value details for this test case.

        Use this method to set the expected details for the return value of a valid method call.
        This method does not validate the input but any non-None values should be valid.

        Args:
            exp_ndim: [OPTIONAL] Sets self._exp_ret_ndim.  A value of None skips this check.
            exp_shape: [OPTIONAL] Sets self._exp_ret_shape.  A value of None skips this check.
            exp_dtype: [OPTIONAL] Sets self._exp_ret_dtype.  A value of None skips this check.
        """
        self._exp_return = numpy.ndarray(0)  # Create an empty array for the retval data type check
        self._exp_ret_ndim = exp_ndim
        self._exp_ret_shape = exp_shape
        self._exp_ret_dtype = exp_dtype
        self._defined_expected_results = True  # Shunt around default validation framework

    def validate_ndarray_return_details(self, return_value: numpy.ndarray):
        """Completely validate numpy.ndarray return values of the tested call.

        Tests type, number of dimensions, shape, and data type as specified by the
        exp_ret_* attributes.
        """
        # LOCAL VARIABLES
        def_error = 'Array {} mismatch:'

        # VALIDATE IT
        # Type
        if self.validate_ndarray_return_type(return_value=return_value):
            # Number of dimensions
            if self._exp_ret_ndim is not None and return_value.ndim != self._exp_ret_ndim:
                self._add_test_failure(f'{def_error.format("dimension")} Expected '
                                       f'{self._exp_return.ndim} dimensions '
                                       f'but received {return_value.ndim} instead')
            # Shape
            if self._exp_ret_shape is not None and return_value.shape != self._exp_ret_shape:
                self._add_test_failure(f'{def_error.format("shape")} Expected '
                                       f'{self._exp_return.shape} shape '
                                       f'but received {return_value.shape} instead')
            # Data Type
            if self._exp_ret_dtype is not None and return_value.dtype != self._exp_ret_dtype:
                self._add_test_failure(f'{def_error.format("dtype")} Expected '
                                       f'{self._exp_return.dtype} shape '
                                       f'but received {return_value.dtype} instead')


class NormalModemBPSKModulateUnitTest(ModemBPSKModulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits(self):
        """Single byte, alternating bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_n02_all_zeros(self):
        """Single byte, all zeros."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        bits = b'00000000'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_n03_all_ones(self):
        """Single byte, all ones."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        bits = b'11111111'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_n04_quad_word_random_bits(self):
        """Eight bytes of random bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        bits = generate_bin_bytes(num_bits=8*8)
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_n05_quad_word_random_bits_flipped_mapper(self):
        """Eight bytes of random bits, inverted constellation mapping."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        bits = generate_bin_bytes(num_bits=8*8)
        mapper = {0: 1+0j, 1: -1+0j}  # Standard mapping: {0: -1+0j, 1: 1+0j}
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)


# Leave me be, Pylint.  These are test cases!
# pylint: disable=too-many-public-methods
class ErrorModemBPSKModulateUnitTest(ModemBPSKModulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_bin_bytes_type_none(self):
        """Bad bin_bytes: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = None
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_bin_bytes_type_string(self):
        """Bad bin_bytes: bad type - string."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = '10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_bin_bytes_value_empty(self):
        """Bad bin_bytes: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b''
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'may not be empty')

    def test_e16_bad_bin_bytes_value_non_binary(self):
        """Bad bin_bytes: bad value - non-binary (AKA '...and I thought I saw a 2' -Bender)."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'101010100010101010121011110100101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'Invalid binary value detected')

    def test_e17_bad_mapper_type_list(self):
        """Bad mapper: wrong type - string."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = [-1+0j, 1+0j]  # Should be a dict
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, TypeError,
                                      'argument should have been of type')

    def test_e18_bad_mapper_value_half_a_map(self):
        """Bad mapper: bad value - only one half of a binary mapping."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = {key: BPSK_MAP[key] for key in list(BPSK_MAP)[:1]}  # Only one entry from BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e19_bad_mapper_value_not_a_binary_map(self):
        """Bad mapper: bad value - Quadrature Phase-Shift Keying (QPSK) mapping."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = QPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'The length of the "mapper" dictionary')


class BoundaryModemBPSKModulateUnitTest(ModemBPSKModulateUnitTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_on(self):
        """One bit: on."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        bits = b'1'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b02_one_bit_off(self):
        """One bit: off."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        bits = b'0'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b03_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = 1
        sym_rate = 80
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'argument is not positive')

    def test_b04_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = 4800
        sym_rate = 1
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b05_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b06_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(bits, mapper, ValueError,
                                      'argument is not positive')

    def test_b07_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = float(4800.0)
        sym_rate = float(1.0)
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b08_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        carr_rec = None
        bits = b'10101010'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b09_smallest_everything_on(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        bits = b'1'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b10_smallest_everything_off(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        bits = b'0'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b11_smallest_everything_on_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): on."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        carr_rec = None
        bits = b'1'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_b12_smallest_everything_off_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): off."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        carr_rec = None
        bits = b'0'
        mapper = None  # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)


class SpecialModemBPSKModulateUnitTest(ModemBPSKModulateUnitTest):
    """Special Test Cases."""

    def test_s01_realistic_usage(self):
        """5.03 Demod 101 FoI 2."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        carr_rec = None
        bits = b'10101010'
        mapper = None       # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s02_real_data_rds_set_msg00_a(self):
        """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name 'KONO    '."""
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        carr_rec = None
        bits = self.RDS_SET1_MSG00A
        mapper = None      # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s03_real_data_demod_101_foi_1_preamble(self):
        """5.03 Demod 101 FoI 1 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        carr_rec = None
        bits = self.DEMOD_101_FOI_1_PREAMBLE
        mapper = None       # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s04_real_data_demod_101_foi_1_pdu(self):
        """5.03 Demod 101 FoI 1 PDU."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        carr_rec = None
        bits = self.DEMOD_101_FOI_1_PDU
        mapper = None       # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s05_real_data_demod_101_foi_2_preamble(self):
        """5.03 Demod 101 FoI 2 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        carr_rec = None
        bits = self.DEMOD_101_FOI_2_PREAMBLE
        mapper = None       # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s06_real_data_demod_101_foi_3_preamble(self):
        """5.03 Demod 101 FoI 3 Preamble."""
        samp_rate = 480000  # 5.03 Demod 101 FoI 3 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 3 symbol rate
        carr_rec = None
        bits = self.DEMOD_101_FOI_3_PREAMBLE
        mapper = None       # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s07_real_data_fhss_chan_01_preamble(self):
        """5.05 FHSS Channel 01 Preamble."""
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        carr_rec = None
        bits = self.FHSS_CHANNEL_01_PREAMBLE
        mapper = None         # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s08_valid_rds_group(self):
        """RF JQR 5.03 RDS group."""
        samp_rate = 19000  # RDS sample rate
        sym_rate = 1187.5  # RDS symbol rate
        carr_rec = None
        bits = self.RDS_GROUP1
        mapper = None      # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s09_superfluous_carrier_recovery_obj(self):
        """Added an unnecessary carrier recovery object to the config."""
        samp_rate = 480000       # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800           # 5.03 Demod 101 FoI 1 symbol rate
        carr_rec = CostasLoop()  # Default settings
        bits = self.RDS_GROUP1
        mapper = None            # Defaults to BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s10_weird_mapper_rotated_30_deg(self):
        """Weird mapper: rotated 30° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 6)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s11_weird_mapper_rotated_45_deg(self):
        """Weird mapper: rotated 45° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 4)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s12_weird_mapper_rotated_60_deg(self):
        """Weird mapper: rotated 60° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 3)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s13_weird_mapper_rotated_90_deg(self):
        """Weird mapper: rotated 90° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 2)  # Imaginary values instead of real
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s14_weird_mapper_rotated_120_deg(self):
        """Weird mapper: rotated 120° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi / 3)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s15_weird_mapper_rotated_135_deg(self):
        """Weird mapper: rotated 135° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 4)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s16_weird_mapper_rotated_150_deg(self):
        """Weird mapper: rotated 150° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 6)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s17_weird_mapper_rotated_180_deg(self):
        """Weird mapper: rotated 180° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, numpy.pi)  # Flipped position
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s18_weird_mapper_rotated_210_deg(self):
        """Weird mapper: rotated 210° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 6)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s19_weird_mapper_rotated_225_deg(self):
        """Weird mapper: rotated 225° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 4)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s20_weird_mapper_rotated_240_deg(self):
        """Weird mapper: rotated 240° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 4 * numpy.pi / 3)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s21_weird_mapper_rotated_270_deg(self):
        """Weird mapper: rotated 270° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 2)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s22_weird_mapper_rotated_300_deg(self):
        """Weird mapper: rotated 300° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 3)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s23_weird_mapper_rotated_315_deg(self):
        """Weird mapper: rotated 315° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 4)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s24_weird_mapper_rotated_330_deg(self):
        """Weird mapper: rotated 330° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 11 * numpy.pi / 6)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)

    def test_s25_weird_mapper_rotated_360_deg(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change).

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi)
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_input_return_def(bits, mapper)


if __name__ == '__main__':
    execute_test_cases()
