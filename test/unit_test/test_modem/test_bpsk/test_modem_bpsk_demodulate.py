"""Unit test module for BPSK.demodulate().

Typical Usage:
    python -m test                                 # Run *all* the test cases
    python -m test.unit_test                       # Run *all* the unit test cases
    python -m test.unit_test.test_modem            # Run *all* modem sub-package test cases
    python -m test.unit_test.test_modem.test_bpsk  # Run *all* BPSK test cases
    # Run just these unit tests
    python -m test.unit_test.test_modem.test_bpsk.test_modem_bpsk_demodulate
    # Run just this normal 1 unit test
    python -m test.unit_test.test_modem.test_bpsk.test_modem_bpsk_demodulate -k n01
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
from gallant_input.modem.constants import BPSK_MAP, BPSK_MAP_3GPP_5G, BPSK_MAP_802_11, QPSK_MAP
from gallant_input.modem.matched_filter import MatchedFilter
from gallant_input.synch.costas_loop import CostasLoop
from test.modify import add_awgn, convert_bin_bytes_to_bpsk, generate_bin_bytes, rotate_mapping
from test.unit_test.test_modem.test_bpsk.test_modem_bpsk import ModemBPSKUnitTest


class ModemBPSKDemodulateUnitTest(ModemBPSKUnitTest):
    """Parent class for all BPSK.demodulate() unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RootUnitTest ctor."""
        super().__init__(*args, **kwargs)
        # ATTRIBUTES
        # File-based test input
        self.test_in1 = self.test_bpsk_in1  # BPSK test input 1
        self.test_in2 = self.test_bpsk_in2  # BPSK test input 2

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

        Test author must call self.set_bpsk_ctor_args() *and* self.set_test_input().

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def run_test_exception_input(self, samples: Any, filt: Any, mapper: Any,
                                 exception_type: Exception, exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_bpsk_ctor_args().

        Args:
            sample_rate: Sets the sample_rate argument input.  Accepts any input, bad or otherwise.
            symbol_rate: Sets the symbol_rate argument input.  Accepts any input, bad or otherwise.
            samples: Test case input.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(samples, filt, mapper)
        self.run_test_exception(exception_type=exception_type, exception_msg=exception_msg)

    def run_test_return(self, sample_rate: float, symbol_rate: float,
                        carrier_recovery: CostasLoop | None, exp_ret: bytes) -> None:
        """Common method calls for a test case expected to return.

        Test author must call self.set_test_input().

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            carrier_recovery: Sets the carrier_recovery ctor argument input.
            exp_ret: The expected return value from the method call.
        """
        self.set_bpsk_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                carrier_recovery=carrier_recovery)
        self.expect_return(exp_ret)
        self.run_test()

    def run_test_return_compute(self, sample_rate: float, symbol_rate: float,
                                carrier_recovery: CostasLoop | None, exp_ret: bytes,
                                filt: MatchedFilter = MatchedFilter.NONE,
                                bit_map: dict[int, complex] | None = None) -> None:
        """Common method calls for a test case expected to return a computed result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            carrier_recovery: Sets the carrier_recovery ctor argument input.
            exp_ret: Expected return value (also used to compute the test case input).
            bit_map: [OPTIONAL] The mapping of symbols to complex values to generate IQ.
                If None, uses the default mapping.
        """
        test_in = create_test_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                    bin_bytes=exp_ret, bit_map=bit_map)
        self.run_test_return_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                   carrier_recovery=carrier_recovery, samples=test_in,
                                   exp_ret=exp_ret, filt=filt, mapper=bit_map)

    def run_test_return_file(self, sigmf_input: Path,
                             sample_dtype: DTypeLike = numpy.complex64) -> None:
        """Common method calls for a test expected to return using file-based test input.

        The test author *must* call set_bpsk_ctor_args().

        Args:
            sigmf_input: The file to use as a source of samples and expected result.
            sample_dtype: The samples data type.
        """
        self.set_test_file_input(sigmf_input=sigmf_input, sample_dtype=sample_dtype)
        self.run_test()

    def run_test_return_input(self, sample_rate: float, symbol_rate: float,
                              carrier_recovery: CostasLoop | None, samples: numpy.ndarray,
                              exp_ret: bytes, filt: MatchedFilter = MatchedFilter.NONE,
                              mapper: dict[int, complex] | None = None) -> None:
        """Common method calls for a test case expected to return an expected result.

        Args:
            sample_rate: Sets the sample_rate ctor argument input.
            symbol_rate: Sets the symbol_rate ctor argument input.
            carrier_recovery: Sets the carrier_recovery ctor argument input.
            samples: Test case input.
            exp_ret: The expected return value from the method call.
            filt: [OPTIONAL] Test case input.
            mapper: [OPTIONAL] Test case input.
        """
        self.set_test_input(samples, filt, mapper)
        self.run_test_return(sample_rate=sample_rate, symbol_rate=symbol_rate,
                             carrier_recovery=carrier_recovery, exp_ret=exp_ret)

    def run_test_return_noisy(self, sample_rate: float, symbol_rate: float,
                              carrier_recovery: CostasLoop | None,
                              exp_ret: bytes, snr_db: float | int,
                              filt: MatchedFilter = MatchedFilter.NONE,
                              mapper: dict[int, complex] | None = None) -> None:
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
                                          bin_bytes=exp_ret, snr_db=snr_db)
        self.run_test_return_input(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                   samples=test_in, filt=filt, carrier_recovery=carrier_recovery,
                                   exp_ret=exp_ret, mapper=mapper)


class NormalModemBPSKDemodulateUnitTest(ModemBPSKDemodulateUnitTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits(self):
        """Single byte, alternating bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = b'10101010'
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, exp_ret)

    def test_n02_one_byte_off_one_byte_on(self):
        """One pair of alternating bytes: off, on."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = b'0000000011111111'
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, exp_ret)

    def test_n03_one_byte_on_one_byte_off(self):
        """One pair of alternating bytes: on, off."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = b'1111111100000000'
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, exp_ret)

    def test_n04_single_byte_alt_bits_with_awgn(self):
        """Single byte, alternating bits, with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = b'10101010'
        snr_db = self.SNR_POOR
        self.run_test_return_noisy(samp_rate, sym_rate, carr_rec, exp_ret, snr_db)

    def test_n05_one_byte_off_one_byte_on_with_awgn(self):
        """One pair of alternating bytes: off, on; with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = b'0000000011111111'
        snr_db = self.SNR_POOR
        self.run_test_return_noisy(samp_rate, sym_rate, carr_rec, exp_ret, snr_db)

    def test_n06_one_byte_on_one_byte_off_with_awgn(self):
        """One pair of alternating bytes: on, off; with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = b'1111111100000000'
        snr_db = self.SNR_POOR
        self.run_test_return_noisy(samp_rate, sym_rate, carr_rec, exp_ret, snr_db)

    @skip('This input requires symbol synch and carrier recovery to pass')
    def test_n07_valid_bpsk_sigmf_demod101_foi1_rates(self):
        """Demod 101 FoI 1 decimated, filtered, and exported."""
        samp_rate = 4800  # 5.03 Demod 101 FoI 1 sample rate (decimated)
        sym_rate = 1200   # 5.03 Demod 101 FoI 3 symbol rate
        carr_rec = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_file(self.test_in1)

    @skip('This input requires symbol synch, carrier recover, and differential decoding to pass')
    def test_n08_valid_bpsk_sigmf_rds_traffic(self):
        """Really distinct signal (AKA Radio Data System) filtered, and exported."""
        samp_rate = 19000  # Really distinct signal sample rate (*not* decimated)
        sym_rate = 1187.5  # Really distinct signal symbol rate
        carr_rec = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_file(self.test_in2)

    def test_n09_random_bits(self):
        """Random bits."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = generate_bin_bytes(num_bits=128)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, exp_ret)

    def test_n10_random_bits_with_awgn(self):
        """Random bits with AWGN at a reasonable SNR (dB)."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        exp_ret = generate_bin_bytes(num_bits=128)
        snr_db = self.SNR_POOR
        self.run_test_return_noisy(samp_rate, sym_rate, carr_rec, exp_ret, snr_db)

    def test_n11_3gpp_5g_mapping(self):
        """3GPP 5G standard BPSK mapping."""
        samp_rate = 4800
        sym_rate = 1000
        carr_rec = None
        mapper = BPSK_MAP_3GPP_5G
        exp_ret = generate_bin_bytes(num_bits=256)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, exp_ret, bit_map=mapper)

    def test_n12_802_11_mapping(self):
        """IEEE 802.11 standard BPSK mapping."""
        samp_rate = 48000
        sym_rate = 1000
        carr_rec = None
        mapper = BPSK_MAP_802_11
        exp_ret = generate_bin_bytes(num_bits=256)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, exp_ret, bit_map=mapper)


# They're test cases, Pylint.  Leave me be.
# pylint: disable=too-many-public-methods
class ErrorModemBPSKDemodulateUnitTest(ModemBPSKDemodulateUnitTest):
    """Error Test Cases."""

    def test_e01_bad_sample_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = None
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_ONES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument must be a')

    def test_e02_bad_sample_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = '48000'
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument must be a')

    def test_e03_bad_sample_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 0
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e04_bad_sample_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = -48000
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_01S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "sample_rate" argument is not positive')

    def test_e05_bad_sample_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = float(0.0)
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_ONES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "sample_rate" argument may not be 0')

    def test_e06_bad_sample_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = float(-48000.0)
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "sample_rate" argument *must* be > 0')

    def test_e07_bad_symbol_rate_type_none(self):
        """Bad sample rate: wrong type - None."""
        samp_rate = 48000
        sym_rate = None
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument must be a')

    def test_e08_bad_symbol_rate_type_string(self):
        """Bad sample rate: wrong type - string."""
        samp_rate = 48000
        sym_rate = '800'
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_01S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument must be a')

    def test_e09_bad_symbol_rate_value_zero(self):
        """Bad sample rate: bad value - zero."""
        samp_rate = 48000
        sym_rate = 0
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_ONES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e10_bad_symbol_rate_value_negative(self):
        """Bad sample rate: bad value - negative."""
        samp_rate = 48000
        sym_rate = -800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "symbol_rate" argument is not positive')

    def test_e11_bad_symbol_rate_value_zero_float(self):
        """Bad sample rate: bad value - float(zero)."""
        samp_rate = 48000
        sym_rate = float(0.0)
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "symbol_rate" argument may not be 0')

    def test_e12_bad_symbol_rate_value_negative_float(self):
        """Bad sample rate: bad value - float(negative)."""
        samp_rate = 48000
        sym_rate = float(-800.0)
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_01S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The "symbol_rate" argument *must* be > 0')

    def test_e13_bad_samples_type_none(self):
        """Bad samples: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = None
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_samples_type_complex_list(self):
        """Bad samples: bad type - list of complex values (almost an ndarray)."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = [0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j, 0.+0.j, 1.+0.j]
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_samples_value_empty(self):
        """Bad samples: bad value - empty."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = numpy.array([], dtype=numpy.complex64)  # len(test_in) == 0
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'ndarray may not be empty')

    def test_e16_bad_samples_invalid_dimensions(self):
        """Bad samples: wrong dimensions."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = numpy.resize(self.SAMPLES_OOK_ALL_10S, (2, 2))  # test_in.ndim == 2
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      f'value is {test_in.ndim}-dimensional instead of '
                                      f'{self.SAMPLES_OOK_ALL_10S.ndim}-dimensional')

    def test_e17_bad_carrier_recovery_type_complex_str(self):
        """Bad carrier_recover: bad type - string."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = 'CostasLoop'
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, NotImplementedError,
                                      'Received an unsupported "carrier recovery" object')

    def test_e18_bad_carrier_recovery_content_loop_band(self):
        """Bad carrier_recover: bad content - loop bandwidth."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = CostasLoop(loop_bandwidth='0.01')
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e19_bad_carrier_recovery_content_damp_fact(self):
        """Bad carrier_recover: bad content - damping factor."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = CostasLoop(damping_factor='0.707')
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e13_bad_filt_type_none(self):
        """Bad filt: bad type - None."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = None  # As opposed to MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e14_bad_filt_type_str(self):
        """Bad filt: bad type - string."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.RRC.name  # As opposed to MatchedFilter.RRC
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e15_bad_filt_type_int(self):
        """Bad filt: bad type - int."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.RECT_FIR.real  # As opposed to MatchedFilter.RECT_FIR
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e16_bad_mapper_type_list(self):
        """Bad mapper: wrong type - list."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.RECT_FIR
        mapper = [-1+0j, 1+0j]  # Should be a dict
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, TypeError,
                                      'argument should have been of type')

    def test_e17_bad_mapper_value_half_a_map(self):
        """Bad mapper: bad value - only one half of a binary mapping."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.RECT_FIR
        mapper = {key: BPSK_MAP[key] for key in list(BPSK_MAP)[:1]}  # Only one entry from BPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The length of the "mapper" dictionary')

    def test_e18_bad_mapper_value_not_a_binary_map(self):
        """Bad mapper: bad value - Quadrature Phase-Shift Keying (QPSK) mapping."""
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        test_in = self.SAMPLES_OOK_ALL_10S
        filt_in = MatchedFilter.RECT_FIR
        mapper = QPSK_MAP
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'The length of the "mapper" dictionary')
# pylint: enable=too-many-public-methods


class BoundaryModemBPSKDemodulateUnitTest(ModemBPSKDemodulateUnitTest):
    """Boundary Test Cases."""

    def test_b01_lowest_sample_rate(self):
        """Smallest valid sample rate.

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = 1
        sym_rate = 80
        carr_rec = None
        # Test case input
        test_in = self.SAMPLES_OOK_ALL_ONES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'argument is not positive')

    def test_b02_lowest_sample_rate_floats(self):
        """Smallest valid sample rate (as floats).

        Rounding this computed samples per symbol to an integer results in a value of 0 which is
        not valid.
        """
        samp_rate = float(1.0)
        sym_rate = float(80.0)
        carr_rec = None
        # Test case input
        test_in = self.SAMPLES_OOK_ALL_ZEROES
        filt_in = MatchedFilter.NONE
        mapper = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception_input(test_in, filt_in, mapper, ValueError,
                                      'argument is not positive')


class SpecialModemBPSKDemodulateUnitTest(ModemBPSKDemodulateUnitTest):
    """Special Test Cases."""

    def test_s01_carrier_recovery_costas_loop(self):
        """Random bits; carrier recovery: Costas Loop."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = CostasLoop()
        exp_ret = generate_bin_bytes(num_bits=128)
        filt_in = MatchedFilter.NONE
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, exp_ret, filt=filt_in)

    def test_s02_carrier_recovery_of_random_bits_with_awgn(self):
        """Random bits with AWGN at a reasonable SNR (dB) using a Costas Loop."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = CostasLoop()
        exp_ret = generate_bin_bytes(num_bits=128)
        snr_db = self.SNR_POOR
        filt_in = MatchedFilter.NONE
        self.run_test_return_noisy(samp_rate, sym_rate, carr_rec, exp_ret, snr_db, filt=filt_in)

    def test_s03_everything_everywhere_all_at_once(self):
        """Random AWGN bits, at a reasonable SNR (dB), using a Costas Loop and rectangular FIR."""
        samp_rate = 4800
        sym_rate = 80
        carr_rec = CostasLoop()
        exp_ret = generate_bin_bytes(num_bits=256)
        snr_db = self.SNR_POOR
        filt_in = MatchedFilter.RECT_FIR
        self.run_test_return_noisy(samp_rate, sym_rate, carr_rec, exp_ret, snr_db, filt=filt_in)

    def test_s04_weird_mapper_rotated_30_deg(self):
        """Weird mapper: rotated 30° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 6)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s05_weird_mapper_rotated_45_deg(self):
        """Weird mapper: rotated 45° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 4)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s06_weird_mapper_rotated_60_deg(self):
        """Weird mapper: rotated 60° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 3)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s07_weird_mapper_rotated_90_deg(self):
        """Weird mapper: rotated 90° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 2)  # Imaginary values instead of real
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s08_weird_mapper_rotated_120_deg(self):
        """Weird mapper: rotated 120° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi / 3)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s09_weird_mapper_rotated_135_deg(self):
        """Weird mapper: rotated 135° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 4)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s10_weird_mapper_rotated_150_deg(self):
        """Weird mapper: rotated 150° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 6)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s11_weird_mapper_rotated_180_deg(self):
        """Weird mapper: rotated 180° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, numpy.pi)  # Flipped position
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s12_weird_mapper_rotated_210_deg(self):
        """Weird mapper: rotated 210° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 6)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s13_weird_mapper_rotated_225_deg(self):
        """Weird mapper: rotated 225° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 4)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s14_weird_mapper_rotated_240_deg(self):
        """Weird mapper: rotated 240° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 4 * numpy.pi / 3)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s15_weird_mapper_rotated_270_deg(self):
        """Weird mapper: rotated 270° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 2)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s16_weird_mapper_rotated_300_deg(self):
        """Weird mapper: rotated 300° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 3)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s17_weird_mapper_rotated_315_deg(self):
        """Weird mapper: rotated 315° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 4)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s18_weird_mapper_rotated_330_deg(self):
        """Weird mapper: rotated 330° on the complex plane.

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 11 * numpy.pi / 6)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)

    def test_s19_weird_mapper_rotated_360_deg(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change).

        Binary mapping rotated away from the real axis on the complex plane.
        """
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        bits = b'10101010'
        filt_in = MatchedFilter.NONE
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi)
        self.run_test_return_compute(samp_rate, sym_rate, carr_rec, bits, filt_in, mapper)


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
            If None, uses BPSK_MAP (see: gallant_input.modem.constants).
    """
    mapping = bit_map
    if mapping is None:
        mapping = BPSK_MAP
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
            If None, uses BPSK_MAP (see: gallant_input.modem.constants).
    """
    mapping = bit_map
    if mapping is None:
        mapping = BPSK_MAP
    return convert_bin_bytes_to_bpsk(bin_bytes=bin_bytes, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate, bit_map=mapping)


if __name__ == '__main__':
    execute_test_cases()
