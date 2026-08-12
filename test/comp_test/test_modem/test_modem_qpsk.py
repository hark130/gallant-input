"""Defines the base modem.qpsk QPSK() Component Test Class.

Typical Usage:
    python -m test                                       # Run *all* the test cases
    python -m test.comp_test                             # Run *all* the component test cases
    python -m test.comp_test.test_modem                  # Run *all* modem sub-package test cases
    python -m test.comp_test.test_modem.test_modem_qpsk  # Run *all* QPSK test cases
    # Run just this normal 1 unit test
    python -m test.comp_test.test_modem.test_modem_qpsk -k n01
"""

# Standard Imports
from typing import Any
from unittest import skip
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from gallant_input.modem.qpsk import QPSK
from gallant_input.modem.qpsk_config import QPSKConfig
from gallant_input.modem.constants import QPSK_MAP
from gallant_input.modem.matched_filter import MatchedFilter
from test.comp_test.test_modem.modem_comp_test import ModemCompTest
from test.modify import add_awgn, convert_bin_bytes_to_qpsk, generate_bin_bytes, rotate_mapping


# pylint: disable=too-many-instance-attributes
# Leave me be, Pylint
class QPSKModemCompTest(ModemCompTest):
    """GAIN.modem.qpsk QPSK() component test class.

    Defines functionality needed to run component tests on the QPSK() modem class.
    """

    bits_per_symbol = 2  # QPSK == 4PSK == 2^2PSK

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """QPSKModemCompTest ctor."""
        super().__init__(*args, **kwargs)

        # ATTRIBUTES
        self.input_carrier_recovery = None  # Optional QPSKConfig attribute
        self.input_mapper = None            # Optional QPSKConfig attribute
        self._demod_arg_s = None            # Test case input: QPSK().demodulate(samples) arg
        self._demod_arg_f = None            # Test case input: QPSK().demodulate(filt) arg
        self._mod_arg_bb = None             # Test case input: QPSK().modulate(bin_bytes) arg
        self._modem_call_order = True       # Call order for the two methods: If True, mo --> dem
        # self._snr_db = None                 # Optional value to add noise to an array of samples

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        # LOCAL VARIABLES
        test_obj = self.create_test_obj()  # Test case object
        mod_ret_val = None                 # The modulated data as a numpy.ndarray
        demod_ret_val = None               # The demodulated data as a bin bytes obj
        test_result = None                 # Return value depends on _modem_call_order

        # CALL IT
        if self._modem_call_order is True:
            mod_ret_val = test_obj.modulate(self._mod_arg_bb)
            demod_ret_val = test_obj.demodulate(mod_ret_val, self._demod_arg_f)
            test_result = demod_ret_val
        else:
            demod_ret_val = test_obj.demodulate(self._demod_arg_s, self._demod_arg_f)
            mod_ret_val = test_obj.modulate(demod_ret_val)
            test_result = mod_ret_val

        # DONE
        return test_result

    def set_qpsk_ctor_args(self, sample_rate: Any, symbol_rate: Any, carrier_recovery: Any,
                           mapper: Any) -> None:
        """Sets the QPSK() argument values in the test class."""
        self.set_modem_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.input_carrier_recovery = carrier_recovery
        self.input_mapper = mapper

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call.

        Actual return value comparison is controlled by self._modem_call_order.
        """
        if self._modem_call_order is True:
            self.validate_bin_bytes_return_value(return_value=return_value)
        else:
            self.validate_ndarray_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in "suggested" call order

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def run_test_exception(self, exception_type: Exception, exception_msg: str,
                           bin_bytes: Any, samples: Any, filt: Any,
                           modem_order: bool = True) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_qpsk_ctor_args() *and* self.set_test_input().

        Args:
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
            bin_bytes: Test case input for the modulate method argument of the same name.
            mapper: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self.set_oob_test_input(bin_bytes, samples, filt, modem_order)
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return_input(self, bin_bytes: Any, samples: Any, filt: Any,
                              modem_order: bool = True) -> None:
        """Common method calls for a test case expected to return an expected result.

        The expected results depends on modem_order.  Test author must first call
        self.set_modem_ctor_args().

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples,
                                   filt=filt, modem_order=modem_order)
        self.run_test()

    def run_test_return_noisy_input(self, bin_bytes: Any, samples: Any, filt: Any,
                                    snr_db: float | int, modem_order: bool = False) -> None:
        """Common method for a test case expected to return an expected result on noisy input.

        The expected results depends on modem_order.  Test author must first call
        self.set_qpsk_ctor_args().  The modem order will always be False and bin_bytes will
        be None (or else, why create noisy samples just to ignore them?).

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            snr_db: The desigred SNR, in decibels, to add to samples.
            modem_order: [OPTIONAL] This method was written with the assumption that the noisy
                samples will be demodulated and then modulated again.
        """
        noisy = add_awgn(samples, snr_db)
        self.set_test_input_return(bin_bytes=bin_bytes, samples=noisy, filt=filt,
                                   modem_order=modem_order, skip_exp_ret=True)
        self.expect_return(samples)
        self.run_test()
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def set_demodulate_test_input(self, samples: Any, filt: Any) -> None:
        """Sets test case input for the call to the demodulate() method.

        Args:
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
        """
        self._demod_arg_s = samples
        self._demod_arg_f = filt
        self._defined_test_input = True

    def set_modulate_test_input(self, bin_bytes: Any) -> None:
        """Sets test case input for the call to the modulate() method.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
        """
        self._mod_arg_bb = bin_bytes
        self._defined_test_input = True

    def set_oob_test_input(self, bin_bytes: Any, samples: Any,
                           filt: Any, modem_order: bool = True) -> None:
        """Sets out-of-band test case input for both method calls and sets the test case call order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self._validate_type(modem_order, 'modem_order', bool)
        self.set_modulate_test_input(bin_bytes=bin_bytes)
        self.set_demodulate_test_input(samples=samples, filt=filt)
        self._modem_call_order = modem_order

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def set_test_input_return(self, bin_bytes: Any, samples: Any, filt: Any,
                              modem_order: bool = True, skip_exp_ret: bool = False) -> None:
        """Sets test case input for both method calls, test case call order, and expected results.

        The expected results depends on modem_order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
            skip_exp_ret: [OPTIONAL] If True, the test author must call self.expect_return().
        """
        self.set_oob_test_input(bin_bytes, samples, filt, modem_order)
        if not skip_exp_ret:
            if modem_order:
                self.expect_return(bin_bytes)
            else:
                self.expect_return(samples)
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def create_test_obj(self) -> QPSK:
        """Create an QPSK() test object.

        Strongly consider calling self.set_modem_ctor_args() and self.set_qpsk_ctor_args() first.
        """
        config = None  # QPSK() ctor argument
        config = QPSKConfig(sample_rate=self.input_sample_rate, symbol_rate=self.input_symbol_rate,
                            carrier_recovery=self.input_carrier_recovery, mapper=self.input_mapper)
        return QPSK(config=config)
# pylint: enable=too-many-instance-attributes


class NormalQPSKModemCompTest(QPSKModemCompTest):
    """Normal Test Cases."""

    def test_n01_single_word_random_bits_mo_dem(self):
        """Single byte of random bits, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=1*8)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_n02_half_word_random_bits_mo_dem(self):
        """Two bytes of random bits, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_n03_double_word_random_bits_mo_dem(self):
        """Four bytes of random bits, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=4*8)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_n04_quad_word_random_bits_mo_dem(self):
        """Eight bytes of random bits, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=8*8)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_n05_single_word_random_bits_dem_mo(self):
        """Single byte of random bits, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QPSK_MAP  # Used by test code "double do" helper function
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=1*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_n06_single_word_random_bits_dem_mo(self):
        """Two bytes of random bits, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QPSK_MAP  # Used by test code "double do" helper function
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_n07_single_word_random_bits_dem_mo(self):
        """Four bytes of random bits, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QPSK_MAP  # Used by test code "double do" helper function
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=4*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_n08_single_word_random_bits_dem_mo(self):
        """Eight bytes of random bits, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QPSK_MAP  # Used by test code "double do" helper function
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=8*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_n09_random_bits_filtered_mo_dem(self):
        """Random bits, matched filter: rectangular FIR, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.RECT_FIR
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_n10_random_bits_filtered_dem_mo(self):
        """Random bits, matched filter: rectangular FIR, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QPSK_MAP  # Used by test code "double do" helper function
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.RECT_FIR
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    @skip("Test framework doesn't support this specific type of instrumentation")
    def test_n11_random_bits_noisy_mo_dem(self):
        """Random bits w/ AWGN, at a reasonable SNR, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.RECT_FIR
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_noisy_input(bin_bytes=bin_bytes, samples=samples, filt=filt,
                                         snr_db=self.SNR_POOR, modem_order=True)

    def test_n12_random_bits_noisy_dem_mo(self):
        """Random bits w/ AWGN, at a reasonable SNR, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        mapper = QPSK_MAP  # Used by test code "double do" helper function
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_noisy_input(bin_bytes=bin_bytes, samples=samples, filt=filt,
                                         snr_db=self.SNR_POOR, modem_order=False)


class BoundaryQPSKModemCompTest(QPSKModemCompTest):
    """Boundary Test Cases."""

    def test_b01_lowest_symbol_rate_mo_dem(self):
        """Smallest symbol rate, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 1
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_b02_lowest_symbol_rate_dem_mo(self):
        """Smallest symbol rate, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 1
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_b03_samples_per_symbol_smallest_mo_dem(self):
        """Samples per symbol smallest value to be successful, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 3
        sym_rate = 1
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_b04_samples_per_symbol_smallest_dem_mo(self):
        """Samples per symbol smallest value to be successful, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 3
        sym_rate = 1
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_b05_samples_per_symbol_almost_too_small_mo_dem(self):
        """Samples per symbol (almost?!) too small to be successful, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_b06_samples_per_symbol_almost_too_small_dem_mo(self):
        """Samples per symbol (almost?!) too small to be successful, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_b07_samples_per_symbol_too_small_mo_dem(self):
        """Samples per symbol too small to be successful, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 49
        sym_rate = 50
        carr_rec = None
        mapper = None  # Defaults to QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = None
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception(ValueError, 'argument is not positive',
                                bin_bytes, samples, filt, modem_order=True)

    def test_b08_samples_per_symbol_too_small_dem_mo(self):
        """Samples per symbol too small to be successful, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 50
        sym_rate = 51
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_exception(ValueError, 'argument is not positive',
                                bin_bytes, samples, filt, modem_order=False)


class SpecialQPSKModemCompTest(QPSKModemCompTest):
    """Special Test Cases."""

    # They're test cases!  Leave me be, Pylint.
    # pylint: disable=too-many-public-methods
    def test_s01_weird_mapper_rotated_30_deg_mo_dem(self):
        """Weird mapper: rotated 30° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s02_weird_mapper_rotated_45_deg_mo_dem(self):
        """Weird mapper: rotated 45° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s03_weird_mapper_rotated_60_deg_mo_dem(self):
        """Weird mapper: rotated 60° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s04_weird_mapper_rotated_90_deg_mo_dem(self):
        """Weird mapper: rotated 90° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 2)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s05_weird_mapper_rotated_120_deg_mo_dem(self):
        """Weird mapper: rotated 120° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s06_weird_mapper_rotated_135_deg_mo_dem(self):
        """Weird mapper: rotated 135° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s07_weird_mapper_rotated_150_deg_mo_dem(self):
        """Weird mapper: rotated 150° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s08_weird_mapper_rotated_180_deg_mo_dem(self):
        """Weird mapper: rotated 180° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi)  # Flipped position
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s09_weird_mapper_rotated_210_deg_mo_dem(self):
        """Weird mapper: rotated 210° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s10_weird_mapper_rotated_225_deg_mo_dem(self):
        """Weird mapper: rotated 225° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s11_weird_mapper_rotated_240_deg_mo_dem(self):
        """Weird mapper: rotated 240° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 4 * numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s12_weird_mapper_rotated_270_deg_mo_dem(self):
        """Weird mapper: rotated 270° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 2)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s13_weird_mapper_rotated_300_deg_mo_dem(self):
        """Weird mapper: rotated 300° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s14_weird_mapper_rotated_315_deg_mo_dem(self):
        """Weird mapper: rotated 315° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s15_weird_mapper_rotated_330_deg_mo_dem(self):
        """Weird mapper: rotated 330° on the complex plane, mo --> dem order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 11 * numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s16_weird_mapper_rotated_360_deg_mo_dem(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change)."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=True)

    def test_s17_weird_mapper_rotated_30_deg_dem_mo(self):
        """Weird mapper: rotated 30° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s18_weird_mapper_rotated_45_deg_dem_mo(self):
        """Weird mapper: rotated 45° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s19_weird_mapper_rotated_60_deg_dem_mo(self):
        """Weird mapper: rotated 60° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s20_weird_mapper_rotated_90_deg_dem_mo(self):
        """Weird mapper: rotated 90° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi / 2)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s21_weird_mapper_rotated_120_deg_dem_mo(self):
        """Weird mapper: rotated 120° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s22_weird_mapper_rotated_135_deg_dem_mo(self):
        """Weird mapper: rotated 135° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s23_weird_mapper_rotated_150_deg_dem_mo(self):
        """Weird mapper: rotated 150° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s24_weird_mapper_rotated_180_deg_dem_mo(self):
        """Weird mapper: rotated 180° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, numpy.pi)  # Flipped position
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s25_weird_mapper_rotated_210_deg_dem_mo(self):
        """Weird mapper: rotated 210° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s26_weird_mapper_rotated_225_deg_dem_mo(self):
        """Weird mapper: rotated 225° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s27_weird_mapper_rotated_240_deg_dem_mo(self):
        """Weird mapper: rotated 240° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 4 * numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s28_weird_mapper_rotated_270_deg_dem_mo(self):
        """Weird mapper: rotated 270° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 3 * numpy.pi / 2)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s29_weird_mapper_rotated_300_deg_dem_mo(self):
        """Weird mapper: rotated 300° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 5 * numpy.pi / 3)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s30_weird_mapper_rotated_315_deg_dem_mo(self):
        """Weird mapper: rotated 315° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 7 * numpy.pi / 4)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s31_weird_mapper_rotated_330_deg_dem_mo(self):
        """Weird mapper: rotated 330° on the complex plane, dem --> mo order."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 11 * numpy.pi / 6)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s32_weird_mapper_rotated_360_deg_dem_mo(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change)."""
        # QPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        mapper = rotate_mapping(QPSK_MAP, 2 * numpy.pi)
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=256)
        samples = convert_bin_bytes_to_qpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.run_test_return_input(bin_bytes, samples, filt, modem_order=False)

    def test_s33_trailing_zero_needs_padding_mo_dem(self):
        """Modulator binary input doesn't conform to the scheme's expected length: trailing 0.

        Expect trailing zeroes as padding from the demodulator.
        """
        # QPSKConfig() args
        samp_rate = 480000
        sym_rate = 800
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=254) + b'0'  # Total len, 255
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.assertEqual(bin_bytes[len(bin_bytes)-1:], b'0', 'Specifically tests this trailing bit')
        self.assertNotEqual(len(bin_bytes) % self.bits_per_symbol, 0, 'Input length *must* be off')
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples, filt=filt,
                                   modem_order=True, skip_exp_ret=True)
        self.expect_return(bin_bytes + b'0')
        self.run_test()

    def test_s34_trailing_one_needs_padding_mo_dem(self):
        """Modulator binary input doesn't conform to the scheme's expected length: trailing 1.

        Expect trailing zeroes as padding from the modulator.
        """
        # QPSKConfig() args
        samp_rate = 480000
        sym_rate = 800
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=254) + b'1'  # Total len, 255
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.assertEqual(bin_bytes[len(bin_bytes)-1:], b'1', 'Specifically tests this trailing bit')
        self.assertNotEqual(len(bin_bytes) % self.bits_per_symbol, 0, 'Input length *must* be off')
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples, filt=filt,
                                   modem_order=True, skip_exp_ret=True)
        self.expect_return(bin_bytes + b'0')
        self.run_test()

    def test_s35_odd_binary_len_leading_zero_de_mod(self):
        """Samples formed from an odd length input binary expects zero padding: leading 0."""
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = b'0' + generate_bin_bytes(num_bits=254)  # len(bin_bytes) == 255
        filt = MatchedFilter.NONE
        self.assertEqual(bin_bytes[:1], b'0', 'Specifically tests this leading bit')
        self.assertNotEqual(len(bin_bytes) % self.bits_per_symbol, 0, 'Input length *must* be off')
        samples = convert_bin_bytes_to_qpsk(bin_bytes=bin_bytes, sample_rate=samp_rate,
                                            symbol_rate=sym_rate, bit_map=mapper)
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples, filt=filt,
                                   modem_order=False, skip_exp_ret=True)
        self.expect_return(bin_bytes + b'0')  # QPSK output is always even

    def test_s36_odd_binary_len_leading_one(self):
        """Samples formed from an odd length input binary expects zero padding: leading 1."""
        # QPSKConfig() input
        samp_rate = 32000   # GNU Radio tutorial example settings
        sym_rate = 8000     # GNU Radio tutorial example settings
        carr_rec = None
        mapper = QPSK_MAP
        # modulate()/demodulate() args
        bin_bytes = b'1' + generate_bin_bytes(num_bits=254)  # len(bin_bytes) == 255
        filt = MatchedFilter.NONE
        self.assertEqual(bin_bytes[:1], b'1', 'Specifically tests this leading bit')
        self.assertNotEqual(len(bin_bytes) % self.bits_per_symbol, 0, 'Input length *must* be off')
        samples = convert_bin_bytes_to_qpsk(bin_bytes=bin_bytes, sample_rate=samp_rate,
                                            symbol_rate=sym_rate, bit_map=mapper)
        self.set_qpsk_ctor_args(samp_rate, sym_rate, carr_rec, mapper)
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples, filt=filt,
                                   modem_order=False, skip_exp_ret=True)
        self.expect_return(bin_bytes + b'0')  # QPSK output is always even
    # pylint: enable=too-many-public-methods


if __name__ == '__main__':
    execute_test_cases()
