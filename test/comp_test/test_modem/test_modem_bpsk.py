"""Defines the base modem.bpsk BPSK() Component Test Class.

Typical Usage:
    python -m test                                       # Run *all* the test cases
    python -m test.comp_test                             # Run *all* the component test cases
    python -m test.comp_test.test_modem                  # Run *all* modem sub-package test cases
    python -m test.comp_test.test_modem.test_modem_bpsk  # Run *all* BPSK test cases
    # Run just this normal 1 unit test
    python -m test.comp_test.test_modem.test_modem_bpsk -k n01
"""

# Standard Imports
from pathlib import Path
from typing import Any
from unittest import skip
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from gallant_input.modem.bpsk import BPSK
from gallant_input.modem.bpsk_config import BPSKConfig
from gallant_input.modem.constants import BPSK_MAP
from gallant_input.modem.matched_filter import MatchedFilter
from test.comp_test.test_modem.modem_comp_test import ModemCompTest
from test.modify import add_awgn, convert_bin_bytes_to_bpsk, generate_bin_bytes, rotate_mapping


# pylint: disable=too-many-instance-attributes
# Leave me be, Pylint
class BPSKModemCompTest(ModemCompTest):
    """GAIN.modem.bpsk BPSK() component test class.

    Defines functionality needed to run component tests on the BPSK() modem class.
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """BPSKModemCompTest ctor."""
        super().__init__(*args, **kwargs)

        # ATTRIBUTES
        self.carrier_recovery = None   # Optional BPSKConfig attribute
        self._demod_arg_s = None       # Test case input: BPSK().demodulate(samples) arg
        self._demod_arg_f = None       # Test case input: BPSK().demodulate(filt) arg
        self._demod_arg_m = None       # Test case input: BPSK().demodulate(mapper) arg
        self._mod_arg_bb = None        # Test case input: BPSK().modulate(bin_bytes) arg
        self._mod_arg_map = None       # Test case input: BPSK().modulate(mapper) arg
        self._modem_call_order = True  # Call order for the two methods: If True, mo --> dem

    def call_callable(self):
        """Defines how the class will invoke the function call."""
        # LOCAL VARIABLES
        test_obj = self.create_test_obj()  # Test case object
        mod_ret_val = None                 # The modulated data as a numpy.ndarray
        demod_ret_val = None               # The demodulated data as a bin bytes obj
        test_result = None                 # Return value depends on _modem_call_order

        # CALL IT
        if self._modem_call_order is True:
            mod_ret_val = test_obj.modulate(self._mod_arg_bb, self._mod_arg_map)
            demod_ret_val = test_obj.demodulate(mod_ret_val, self._demod_arg_f, self._demod_arg_m)
            test_result = demod_ret_val
        else:
            demod_ret_val = test_obj.demodulate(self._demod_arg_s, self._demod_arg_f,
                                                self._demod_arg_m)
            mod_ret_val = test_obj.modulate(demod_ret_val, self._mod_arg_map)
            test_result = mod_ret_val

        # DONE
        return test_result

    def set_bpsk_ctor_args(self, sample_rate: Any, symbol_rate: Any, carrier_recovery: Any) -> None:
        """Sets the BPSK() argument values in the test class."""
        self.set_modem_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.carrier_recovery = carrier_recovery

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

    def run_test_exception(self, exception_type: Exception, exception_msg: str,
                           bin_bytes: Any, mapper: Any, samples: Any, filt: Any,
                           modem_order: bool = True) -> None:
        """Common method calls for a test case expected to raise an exception.

        Test author must call self.set_bpsk_ctor_args() *and* self.set_test_input().

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
        self.set_oob_test_input(bin_bytes, mapper, samples, filt, modem_order)
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return_input(self, bin_bytes: Any, mapper: Any, samples: Any, filt: Any,
                              modem_order: bool = True) -> None:
        """Common method calls for a test case expected to return an expected result.

        The expected results depends on modem_order.  Test author must first call
        self.set_modem_ctor_args().

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            mapper: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self.set_test_input_return(bin_bytes=bin_bytes, mapper=mapper, samples=samples,
                                   filt=filt, modem_order=modem_order)
        self.run_test()

    def run_test_return_noisy_input(self, samples: Any, filt: Any, snr_db: float | int) -> None:
        """Common method for a test case expected to return an expected result on noisy input.

        The expected results depends on modem_order.  Test author must first call
        self.set_modem_ctor_args().  The modem order will always be False and bin_bytes will
        be None (or else, why create noisy samples just to ignore them?).

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            snr_db: The desigred SNR, in decibels, to add to samples.
        """
        noisy = add_awgn(samples, snr_db)
        self.set_test_input_return(bin_bytes=None, samples=noisy, filt=filt,
                                   modem_order=False, skip_exp_ret=True)
        self.expect_return(samples)
        self.run_test()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def set_demodulate_test_input(self, samples: Any, filt: Any, mapper: Any) -> None:
        """Sets test case input for the call to the demodulate() method.

        Args:
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
        """
        self._demod_arg_s = samples
        self._demod_arg_f = filt
        self._demod_arg_m = mapper
        self._defined_test_input = True

    def set_modulate_test_input(self, bin_bytes: Any, mapper: Any) -> None:
        """Sets test case input for the call to the modulate() method.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            mapper: Test case input for the modulate method argument of the same name.
        """
        self._mod_arg_bb = bin_bytes
        self._mod_arg_map = mapper
        self._defined_test_input = True

    def set_oob_test_input(self, bin_bytes: Any, mapper: Any, samples: Any,
                           filt: Any, modem_order: bool = True) -> None:
        """Sets out-of-band test case input for both method calls and sets the test case call order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            mapper: Test input for the modulate (and demodulate) method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self._validate_type(modem_order, 'modem_order', bool)
        self.set_modulate_test_input(bin_bytes=bin_bytes, mapper=mapper)
        self.set_demodulate_test_input(samples=samples, filt=filt, mapper=mapper)
        self._modem_call_order = modem_order

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def set_test_input_return(self, bin_bytes: Any, mapper: Any, samples: Any, filt: Any,
                              modem_order: bool = True, skip_exp_ret: bool = False) -> None:
        """Sets test case input for both method calls, test case call order, and expected results.

        The expected results depends on modem_order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            mapper: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
            skip_exp_ret: [OPTIONAL] If True, the test author must call self.expect_return().
        """
        self.set_oob_test_input(bin_bytes, mapper, samples, filt, modem_order)
        if not skip_exp_ret:
            if modem_order:
                self.expect_return(bin_bytes)
            else:
                self.expect_return(samples)
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def set_test_file_input_return(self, sigmf_file: Path) -> None:
        """Use a SigMF file as demodulate() --> modulate() samples test case input."""
        samples = None    # Samples read ffrom sigmf_file
        bin_bytes = None  # Description (original digital data) read from sigmf_file's metadata
        samples, bin_bytes = self.get_test_file_input(file_input=sigmf_file, sigmf_data=True)
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples, modem_order=False)

    def create_test_obj(self) -> BPSK:
        """Create an BPSK() test object.

        Strongly consider calling self.set_modem_ctor_args() and self.set_bpsk_ctor_args() first.
        """
        config = None  # BPSK() ctor argument
        config = BPSKConfig(sample_rate=self.input_sample_rate,
                            symbol_rate=self.input_symbol_rate,
                            carrier_recovery=self.carrier_recovery)
        return BPSK(config=config)
# pylint: enable=too-many-instance-attributes


class NormalBPSKModemCompTest(BPSKModemCompTest):
    """Normal Test Cases."""

    def test_n01_single_word_random_bits_mo_dem(self):
        """Single byte of random bits, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=1*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_n02_half_word_random_bits_mo_dem(self):
        """Two bytes of random bits, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_n03_double_word_random_bits_mo_dem(self):
        """Four bytes of random bits, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=4*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_n04_quad_word_random_bits_mo_dem(self):
        """Eight bytes of random bits, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=8*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_n05_single_word_random_bits_dem_mo(self):
        """Single byte of random bits, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=1*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_n06_single_word_random_bits_dem_mo(self):
        """Two bytes of random bits, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_n07_single_word_random_bits_dem_mo(self):
        """Four bytes of random bits, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=4*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_n08_single_word_random_bits_dem_mo(self):
        """Eight bytes of random bits, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=8*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)


class BoundaryBPSKModemCompTest(BPSKModemCompTest):
    """Boundary Test Cases."""

    def test_b01_lowest_symbol_rate_mo_dem(self):
        """Smallest symbol rate, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 1
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_b02_lowest_symbol_rate_dem_mo(self):
        """Smallest symbol rate, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 1
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_b03_samples_per_symbol_smallest_mo_dem(self):
        """Samples per symbol smallest value to be successful, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 3
        sym_rate = 1
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_b04_samples_per_symbol_smallest_dem_mo(self):
        """Samples per symbol smallest value to be successful, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 3
        sym_rate = 1
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_b05_samples_per_symbol_almost_too_small_mo_dem(self):
        """Samples per symbol (almost?!) too small to be successful, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_b06_samples_per_symbol_almost_too_small_dem_mo(self):
        """Samples per symbol (almost?!) too small to be successful, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 1
        sym_rate = 1
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_b07_samples_per_symbol_too_small_mo_dem(self):
        """Samples per symbol too small to be successful, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 49
        sym_rate = 50
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = None  # Defaults to BPSK_MAP
        samples = None
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception(ValueError, 'argument is not positive',
                                bin_bytes, mapper, samples, filt, modem_order=True)

    def test_b08_samples_per_symbol_too_small_dem_mo(self):
        """Samples per symbol too small to be successful, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 50
        sym_rate = 51
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=2*8)
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_exception(ValueError, 'argument is not positive',
                                bin_bytes, mapper, samples, filt, modem_order=False)


class SpecialBPSKModemCompTest(BPSKModemCompTest):
    """Special Test Cases."""

    def test_s01_rds_sized_random_bits_mo_dem(self):
        """Single byte of random bits, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = None  # Defaults to BPSK_MAP
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s02_single_word_random_bits_dem_mo(self):
        """Single byte of random bits, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 4800
        sym_rate = 80
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = BPSK_MAP
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s03_weird_mapper_rotated_30_deg_mo_dem(self):
        """Weird mapper: rotated 30° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 6)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s04_weird_mapper_rotated_45_deg_mo_dem(self):
        """Weird mapper: rotated 45° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 4)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s05_weird_mapper_rotated_60_deg_mo_dem(self):
        """Weird mapper: rotated 60° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 3)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s06_weird_mapper_rotated_90_deg_mo_dem(self):
        """Weird mapper: rotated 90° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 2)  # Imaginary values instead of real
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s07_weird_mapper_rotated_120_deg_mo_dem(self):
        """Weird mapper: rotated 120° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi / 3)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s08_weird_mapper_rotated_135_deg_mo_dem(self):
        """Weird mapper: rotated 135° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 4)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s09_weird_mapper_rotated_150_deg_mo_dem(self):
        """Weird mapper: rotated 150° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 6)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s10_weird_mapper_rotated_180_deg_mo_dem(self):
        """Weird mapper: rotated 180° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi)  # Flipped position
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s11_weird_mapper_rotated_210_deg_mo_dem(self):
        """Weird mapper: rotated 210° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 6)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s12_weird_mapper_rotated_225_deg_mo_dem(self):
        """Weird mapper: rotated 225° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 4)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s13_weird_mapper_rotated_240_deg_mo_dem(self):
        """Weird mapper: rotated 240° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 4 * numpy.pi / 3)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s14_weird_mapper_rotated_270_deg_mo_dem(self):
        """Weird mapper: rotated 270° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 2)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s15_weird_mapper_rotated_300_deg_mo_dem(self):
        """Weird mapper: rotated 300° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 3)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s16_weird_mapper_rotated_315_deg_mo_dem(self):
        """Weird mapper: rotated 315° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 4)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s17_weird_mapper_rotated_330_deg_mo_dem(self):
        """Weird mapper: rotated 330° on the complex plane, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 11 * numpy.pi / 6)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s18_weird_mapper_rotated_360_deg_mo_dem(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change)."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi)
        samples = None  # Will be defined by dynamic test case execution
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=True)

    def test_s19_weird_mapper_rotated_30_deg_dem_mo(self):
        """Weird mapper: rotated 30° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 6)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s20_weird_mapper_rotated_45_deg_dem_mo(self):
        """Weird mapper: rotated 45° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 4)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s21_weird_mapper_rotated_60_deg_dem_mo(self):
        """Weird mapper: rotated 60° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 3)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s22_weird_mapper_rotated_90_deg_dem_mo(self):
        """Weird mapper: rotated 90° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi / 2)  # Imaginary values instead of real
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s23_weird_mapper_rotated_120_deg_dem_mo(self):
        """Weird mapper: rotated 120° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi / 3)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s24_weird_mapper_rotated_135_deg_dem_mo(self):
        """Weird mapper: rotated 135° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 4)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s25_weird_mapper_rotated_150_deg_dem_mo(self):
        """Weird mapper: rotated 150° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 6)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s26_weird_mapper_rotated_180_deg_dem_mo(self):
        """Weird mapper: rotated 180° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, numpy.pi)  # Flipped position
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s27_weird_mapper_rotated_210_deg_dem_mo(self):
        """Weird mapper: rotated 210° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 6)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s28_weird_mapper_rotated_225_deg_dem_mo(self):
        """Weird mapper: rotated 225° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 4)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s29_weird_mapper_rotated_240_deg_dem_mo(self):
        """Weird mapper: rotated 240° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 4 * numpy.pi / 3)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s30_weird_mapper_rotated_270_deg_dem_mo(self):
        """Weird mapper: rotated 270° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 3 * numpy.pi / 2)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s31_weird_mapper_rotated_300_deg_dem_mo(self):
        """Weird mapper: rotated 300° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 5 * numpy.pi / 3)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s32_weird_mapper_rotated_315_deg_dem_mo(self):
        """Weird mapper: rotated 315° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 7 * numpy.pi / 4)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s33_weird_mapper_rotated_330_deg_dem_mo(self):
        """Weird mapper: rotated 330° on the complex plane, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 11 * numpy.pi / 6)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)

    def test_s34_weird_mapper_rotated_360_deg_dem_mo(self):
        """Weird mapper: rotated 360° on the complex plane (effectively, no change)."""
        # BPSKConfig() args
        samp_rate = 48000
        sym_rate = 800
        carr_rec = None
        # modulate()/demodulate() args
        bin_bytes = generate_bin_bytes(num_bits=104*8*4)  # The size of a full RDS Group
        mapper = rotate_mapping(BPSK_MAP, 2 * numpy.pi)
        samples = convert_bin_bytes_to_bpsk(bin_bytes, samp_rate, sym_rate, mapper)
        filt = MatchedFilter.NONE
        self.set_bpsk_ctor_args(samp_rate, sym_rate, carr_rec)
        self.run_test_return_input(bin_bytes, mapper, samples, filt, modem_order=False)


if __name__ == '__main__':
    execute_test_cases()
