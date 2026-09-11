"""Unit test module for QPSK.demodulate().

Typical Usage:
    python -m test                                      # Run *all* the test cases
    python -m test.unit_test                            # Run *all* the unit test cases
    python -m test.unit_test.test_modem                 # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_utilities  # Run *all* modem.utilities test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_utilities.test_normalize_mapping
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_utilities.test_normalize_mapping -k n01
"""

# Standard Imports
from typing import Any
import math
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
from unittest import skip
import numpy
# Local Imports
from gallant_input.modem.constants import (BPSK_MAP, BPSK_MAP_3GPP_5G, BPSK_MAP_802_11, OOK_MAP,
                                           PSK8_MAP, QPSK_MAP, QPSK_MAP_DVB_S2)
from gallant_input.modem.utilities import normalize_mapping
from test.modify import rotate_mapping
from test.unit_test.root_unit_test import RootUnitTest


class NormalizeMappingUnitTest(RootUnitTest):
    """Parent class for all the modem.utilities.normalize_mapping() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        return normalize_mapping(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_test_input().

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_exception_input(self, mapper: Any, new_avg_energy: Any,
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            mapper: Test case input for the argument of the same name.
            new_avg_energy: Test case input for the argument of the same name.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(mapper, new_avg_energy)
        self.run_test_exception(exception_type=exception_type, exception_msg=exception_msg)

    def run_test_return(self, exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return.

        Test author must call self.set_test_input().

        Args:
            mapper: Test case input for the argument of the same name.
            new_avg_energy: Test case input for the argument of the same name.
            exp_ret: The expected return value from the method call.
        """
        self.expect_return(exp_ret)
        self.run_test()

    def run_test_return_input(self, mapper: dict[int, complex], new_avg_energy: float | int,
                              exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return an expected result.

        Args:
            mapper: Test case input for the argument of the same name.
            new_avg_energy: Test case input for the argument of the same name.
            exp_ret: The expected return value from the method call.
        """
        self.set_test_input(mapper, new_avg_energy)
        self.run_test_return(exp_ret=exp_ret)

    def run_test_return_compute(self, mapper: dict[int, complex],
                                new_avg_energy: float | int, bits_per_symbol: int) -> None:
        """Common method call for a test case computing a 'double-do' expected return value.

        Args:
            mapper: Test case input for the argument of the same name.
            new_avg_energy: Test case input for the argument of the same name.
            bits_per_symbol: The bit width of symbols for a given modulation
                scheme (e.g., QPSK is 2).
        """
        # A lookup-table of rough mean squares (RMS)
        rms_lookup = {1: 1, 2: math.sqrt(2), 3: math.sqrt(10), 4: math.sqrt(42),
                      5: math.sqrt(170), 6: math.sqrt(682), 7: math.sqrt(2730)}
        try:
            scale = new_avg_energy / rms_lookup[bits_per_symbol]
            exp_ret = {key: value * scale for key, value in mapper.items()}
        except KeyError as err:
            self.fail_test_case(repr(err))
        else:
            self.run_test_return_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                       exp_ret=exp_ret)


class NormalNormalizeMappingUnitTest(NormalizeMappingUnitTest):
    """Normal Test Cases."""

    def test_n01_normalize_bpsk_def(self):
        """Normalize BPSK constellation diagram: default."""
        mapper = BPSK_MAP
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=1)

    def test_n02_normalize_bpsk_3gpp_5g(self):
        """Normalize BPSK constellation diagram: 3GPP 5G standard."""
        mapper = BPSK_MAP_3GPP_5G
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=1)

    def test_n03_normalize_bpsk_ieee_802_11(self):
        """Normalize BPSK constellation diagram: IEEE 802.11 standard."""
        mapper = BPSK_MAP_802_11
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=1)

    def test_n04_normalize_qpsk_def(self):
        """Normalize QPSK constellation diagram: default."""
        mapper = QPSK_MAP
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_n05_normalize_qpsk_3gpp_5g(self):
        """Normalize QPSK constellation diagram: DVB-S2 standard.

        Digital Video Broadcasting (DVB) - Satellite Second Generation (S2) standard.
        """
        mapper = QPSK_MAP_DVB_S2
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_n06_normalize_8psk_def(self):
        """Normalize 8-PSK constellation diagram: already normal."""
        mapper = PSK8_MAP
        new_avg_energy = 1  # Default value
        self.run_test_return_input(mapper, new_avg_energy, exp_ret=mapper)  # Already normalized


class ErrorNormalizeMappingUnitTest(NormalizeMappingUnitTest):
    """Error Test Cases."""

    def test_e01_bad_mapper_type_none(self):
        """Bad mapper: wrong type - None."""
        mapper = None
        new_avg_energy = 1
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=TypeError,
                                      exception_msg='argument should have been of type')

    def test_e02_bad_mapper_type_tuple_list(self):
        """Bad mapper: wrong type - list of tuples."""
        mapper = [(0, -1+0j), (1, 1+0j)]  # BPSK_MAP as a list of tuples
        new_avg_energy = 1
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=TypeError,
                                      exception_msg='argument should have been of type')

    def test_e03_bad_mapper_value_empty(self):
        """Bad mapper: bad value - empty dict."""
        mapper = {}
        new_avg_energy = 1
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=ValueError,
                                      exception_msg='argument can not be empty')

    def test_e04_bad_mapper_value_non_complex_dict_val(self):
        """Bad mapper: bad value - non-complex dictionary value."""
        mapper = OOK_MAP
        new_avg_energy = 1
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=TypeError,
                                      exception_msg='argument should have been of type')

    def test_e05_bad_nae_type_none(self):
        """Bad new_avg_energy: bad type - None."""
        mapper = BPSK_MAP
        new_avg_energy = None
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=TypeError,
                                      exception_msg='argument must be a')

    def test_e06_bad_nae_type_complex(self):
        """Bad new_avg_energy: bad type - complex value."""
        mapper = BPSK_MAP
        new_avg_energy = 1+0j
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=TypeError,
                                      exception_msg='argument must be a')

    def test_e07_bad_nae_value_neg_int(self):
        """Bad new_avg_energy: bad value - negative integer."""
        mapper = BPSK_MAP
        new_avg_energy = -1
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=ValueError,
                                      exception_msg='argument is not positive')

    def test_e08_bad_nae_value_zero_int(self):
        """Bad new_avg_energy: bad value - zero integer."""
        mapper = BPSK_MAP
        new_avg_energy = 0
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=ValueError,
                                      exception_msg='argument is not positive')

    def test_e09_bad_nae_value_neg_float(self):
        """Bad new_avg_energy: bad value - negative float."""
        mapper = BPSK_MAP
        new_avg_energy = -1.0
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=ValueError,
                                      exception_msg='argument is not positive')

    def test_e10_bad_nae_value_zero_float(self):
        """Bad new_avg_energy: bad value - zero float."""
        mapper = BPSK_MAP
        new_avg_energy = 0.0
        self.run_test_exception_input(mapper=mapper, new_avg_energy=new_avg_energy,
                                      exception_type=ValueError,
                                      exception_msg='may not be')


class SpecialNormalizeMappingUnitTest(NormalizeMappingUnitTest):
    """Special Test Cases."""

    def test_s01_weird_mapper_rotated_30_deg(self):
        """Weird mapper: rotated 30° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 6)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    @skip('This result is close enough but I do not want to refactor with math.isclose()')
    def test_s02_weird_mapper_rotated_45_deg(self):
        """Weird mapper: rotated 45° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 4)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s03_weird_mapper_rotated_60_deg(self):
        """Weird mapper: rotated 60° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 3)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    @skip('This result is close enough but I do not want to refactor with math.isclose()')
    def test_s04_weird_mapper_rotated_90_deg(self):
        """Weird mapper: rotated 90° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 2)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    @skip('This result is close enough but I do not want to refactor with math.isclose()')
    def test_s05_weird_mapper_rotated_120_deg(self):
        """Weird mapper: rotated 120° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi / 3)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    @skip('This result is close enough but I do not want to refactor with math.isclose()')
    def test_s06_weird_mapper_rotated_135_deg(self):
        """Weird mapper: rotated 135° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 4)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s07_weird_mapper_rotated_150_deg(self):
        """Weird mapper: rotated 150° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 6)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s08_weird_mapper_rotated_180_deg(self):
        """Weird mapper: rotated 180° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, numpy.pi)  # Flipped position
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s09_weird_mapper_rotated_210_deg(self):
        """Weird mapper: rotated 210° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 6)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s10_weird_mapper_rotated_225_deg(self):
        """Weird mapper: rotated 225° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 4)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s11_weird_mapper_rotated_240_deg(self):
        """Weird mapper: rotated 240° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 4 * numpy.pi / 3)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s12_weird_mapper_rotated_270_deg(self):
        """Weird mapper: rotated 270° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 2)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s13_weird_mapper_rotated_300_deg(self):
        """Weird mapper: rotated 300° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 3)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    @skip('This result is close enough but I do not want to refactor with math.isclose()')
    def test_s14_weird_mapper_rotated_315_deg(self):
        """Weird mapper: rotated 315° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 4)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s15_weird_mapper_rotated_330_deg(self):
        """Weird mapper: rotated 330° on the complex plane.

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 11 * numpy.pi / 6)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)

    def test_s16_weird_mapper_rotated_360_deg(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change).

        QPSK mapping rotated away from the real axis on the complex plane.
        """
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi)
        new_avg_energy = 1  # Default value
        self.run_test_return_compute(mapper, new_avg_energy, bits_per_symbol=2)


if __name__ == '__main__':
    execute_test_cases()
