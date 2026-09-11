"""Unit test module for QAM16.modulate().

Typical Usage:
    python -m test                                  # Run *all* the test cases
    python -m test.unit_test                        # Run *all* the unit test cases
    python -m test.unit_test.test_modem             # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_qam16  # Run *all* QAM16 test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_qam16.test_modem_qam16_modulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_qam16.test_modem_qam16_modulate -k n01
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from gallant_input.modem.constants import QAM16_MAP, QPSK_MAP
from gallant_input.synch.costas_loop import CostasLoop
from test.modify import convert_bin_bytes_to_qam16, generate_bin_bytes, rotate_mapping
from test.unit_test.test_modem.test_qam16.test_modem_qam16 import ModemQAM16UnitTest


class ModemQAM16ModulateUnitTest(ModemQAM16UnitTest):
    """Parent class for all QAM16.modulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        test_obj = self.create_test_obj()
        return test_obj.modulate(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self.validate_ndarray_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call set_qam16_ctor_args() *and* set_test_input().

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_exception_input(self, bin_bytes: Any,
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case, with input, expected to raise an exception.

        Test author must call set_qam16_ctor_args() *and* set_test_input().

        Args:
            bin_bytes: Test case input.
            mapper: Test case input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(bin_bytes)
        self.run_test_exception(exception_type, exception_msg)

    def run_test_return_compute(self, bin_bytes: bytes) -> None:
        """Common method calls to set the input and compute expected returns for a test case.

        The test author *must* call set_qam16_ctor_args() first.

        Args:
            bin_bytes: Test case input.
        """
        exp_ret = convert_bin_bytes_to_qam16(
            bin_bytes=bin_bytes, sample_rate=self.input_sample_rate,
            symbol_rate=self.input_symbol_rate, bit_map=self.input_mapper)
        self.run_test_return_input(bin_bytes=bin_bytes, exp_ret=exp_ret)

    def run_test_return_input(self, bin_bytes: bytes, exp_ret: numpy.ndarray) -> None:
        """Common method calls to set the input for a test case expected to return.

        The test author *must* call set_qam16_ctor_args() first.

        Args:
            bin_bytes: Test case input.
        """
        self.set_test_input(bin_bytes)
        self.expect_return(exp_ret)
        self.run_test()


class NormalModemQAM16ModulateUnitTest(ModemQAM16ModulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_word_random_bits(self):
        """Single byte of random bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=1*8)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_n02_half_word_random_bits(self):
        """Two bytes of random bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=2*8)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_n03_double_word_random_bits(self):
        """Four bytes of random bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=4*8)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_n04_quad_word_random_bits(self):
        """Eight bytes of random bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=8*8)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_n05_quad_word_repeating_all_symbols(self):
        """Repeating all symbols for eight bytes."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bps = 2                                    # Bits per symbol
        repeat = int(8 * 8 / (bps * len(mapper)))  # Number of repeats
        bits = b''.join([bytes(f'{key:02b}', 'ascii') for key in QAM16_MAP]) * repeat
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)


# Leave me be, Pylint.  These are test cases!
# pylint: disable=too-many-public-methods
class ErrorModemQAM16ModulateUnitTest(ModemQAM16ModulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e13_bad_bin_bytes_type_none(self):
        """Bad bin_bytes: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = None
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_bin_bytes_type_string(self):
        """Bad bin_bytes: bad type - string."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = '10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_bin_bytes_value_empty(self):
        """Bad bin_bytes: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b''
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'may not be empty')

    def test_e16_bad_bin_bytes_value_non_binary(self):
        """Bad bin_bytes: bad value - non-binary (AKA '...and I thought I saw a 2' -Bender)."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'101010100010101010121011110100101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'Invalid binary value detected')

    def test_e17_bad_mapper_type_list(self):
        """Bad mapper: wrong type - list."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = list(QAM16_MAP.values())  # Should be a dict
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, TypeError,
                                      'argument should have been of type')

    def test_e18_bad_mapper_value_too_few_entries(self):
        """Bad mapper: bad value - not enough entries."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = {key: QAM16_MAP[key] for key in list(QAM16_MAP)[:1]}  # Only one map entry
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e19_bad_mapper_value_not_a_full_map(self):
        """Bad mapper: bad value - Quadrature Phase-Shift Keying (QPSK) mapping."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = QPSK_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e20_bad_mapper_value_one_shy_of_a_quad_map(self):
        """Bad mapper: bad value - three-of-four QAM16 mappings."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = {key: QAM16_MAP[key] for key in list(QAM16_MAP)[:len(QAM16_MAP)-1]}  # One shy
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e21_bad_mapper_value_quad_map_plus_one(self):
        """Bad mapper: bad value - QAM16 mapping with an extra entry."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = {**QAM16_MAP, len(QAM16_MAP): (2-2j)}  # Errant entry
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'The length of the "mapper" dictionary')


class BoundaryModemQAM16ModulateUnitTest(ModemQAM16ModulateUnitTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_on(self):
        """One bit: on."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'1'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b02_one_bit_off(self):
        """One bit: off."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'0'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b03_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = 1
        sym_rate = 80
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'argument is not positive')

    def test_b04_lowest_symbol_rate(self):
        """Smallest valid symbol rate."""
        samp_rate = 4800
        sym_rate = 1
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b05_lowest_samples_per_symbol(self):
        """Smallest valid sample rate and symbol rate."""
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b06_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'10101010'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception_input(bits, ValueError,
                                      'argument is not positive')

    def test_b07_lowest_symbol_rate_floats(self):
        """Smallest valid symbol rate (as floats)."""
        samp_rate = float(4800.0)
        sym_rate = float(1.0)
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b08_lowest_samples_per_symbol_floats(self):
        """Smallest valid sample rate and symbol rate (as floats)."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b09_smallest_everything_on(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'1'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b10_smallest_everything_off(self):
        """All arguments are set to the smallest appropriate values: on."""
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'0'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b11_smallest_everything_on_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): on."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'1'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_b12_smallest_everything_off_floats(self):
        """All arguments are set to the smallest appropriate values (as floats): off."""
        samp_rate = float(1.0)
        sym_rate = float(1.0)
        carr_rec = None
        mapper = QAM16_MAP
        bits = b'0'
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)


class SpecialModemQAM16ModulateUnitTest(ModemQAM16ModulateUnitTest):
    """Special Test Cases."""

    def test_s01_weird_mapper_rotated_30_deg(self):
        """Weird mapper: rotated 30° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, numpy.pi / 6)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s02_weird_mapper_rotated_45_deg(self):
        """Weird mapper: rotated 45° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, numpy.pi / 4)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s03_weird_mapper_rotated_60_deg(self):
        """Weird mapper: rotated 60° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, numpy.pi / 3)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s04_weird_mapper_rotated_90_deg(self):
        """Weird mapper: rotated 90° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, numpy.pi / 2)  # Imaginary values instead of real
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s05_weird_mapper_rotated_120_deg(self):
        """Weird mapper: rotated 120° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 2 * numpy.pi / 3)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s06_weird_mapper_rotated_135_deg(self):
        """Weird mapper: rotated 135° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 3 * numpy.pi / 4)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s07_weird_mapper_rotated_150_deg(self):
        """Weird mapper: rotated 150° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 5 * numpy.pi / 6)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s08_weird_mapper_rotated_180_deg(self):
        """Weird mapper: rotated 180° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, numpy.pi)  # Flipped position
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s09_weird_mapper_rotated_210_deg(self):
        """Weird mapper: rotated 210° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 7 * numpy.pi / 6)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s10_weird_mapper_rotated_225_deg(self):
        """Weird mapper: rotated 225° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 5 * numpy.pi / 4)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s11_weird_mapper_rotated_240_deg(self):
        """Weird mapper: rotated 240° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 4 * numpy.pi / 3)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s12_weird_mapper_rotated_270_deg(self):
        """Weird mapper: rotated 270° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 3 * numpy.pi / 2)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s13_weird_mapper_rotated_300_deg(self):
        """Weird mapper: rotated 300° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 5 * numpy.pi / 3)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s14_weird_mapper_rotated_315_deg(self):
        """Weird mapper: rotated 315° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 7 * numpy.pi / 4)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s15_weird_mapper_rotated_330_deg(self):
        """Weird mapper: rotated 330° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 11 * numpy.pi / 6)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s16_weird_mapper_rotated_360_deg(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change).

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QAM16_MAP, 2 * numpy.pi)
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s17_superfluous_carrier_recovery_obj(self):
        """Added an unnecessary carrier recovery object to the config."""
        samp_rate = 480000
        sym_rate = 800
        carr_rec = CostasLoop()  # Default settings
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=256)
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s18_trailing_zero_needs_padding(self):
        """Binary input doesn't conform to the scheme's expected length.

        Expect trailing zeroes as padding from the modulator.
        """
        samp_rate = 480000
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=254) + b'0'  # Total len, 255
        self.assertEqual(bits[len(bits)-1:], b'0', 'Specifically tests this trailing bit')
        self.assertNotEqual(len(bits) % self.bits_per_symbol, 0, 'Input length *must* be off')
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)

    def test_s19_trailing_one_needs_padding(self):
        """Binary input doesn't conform to the scheme's expected length.

        Expect trailing zeroes as padding from the modulator.
        """
        samp_rate = 480000
        sym_rate = 800
        carr_rec = None
        mapper = QAM16_MAP
        bits = generate_bin_bytes(num_bits=254) + b'1'  # Total len, 255
        self.assertEqual(bits[len(bits)-1:], b'1', 'Specifically tests this trailing bit')
        self.assertNotEqual(len(bits) % self.bits_per_symbol, 0, 'Input length *must* be off')
        self.set_qam16_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_compute(bits)


if __name__ == '__main__':
    execute_test_cases()
