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
# Local Imports
from gallant_input.modem.bpsk import BPSK
from gallant_input.modem.bpsk_config import BPSKConfig
from gallant_input.modem.constants import BPSK_MAP
from gallant_input.modem.matched_filter import MatchedFilter
from test.comp_test.test_modem.modem_comp_test import ModemCompTest
from test.modify import add_awgn, convert_bin_bytes_to_bpsk, generate_bin_bytes


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
            mod_ret_val = test_obj.modulate(self._mod_arg_bb)
            demod_ret_val = test_obj.demodulate(mod_ret_val)
            test_result = demod_ret_val
        else:
            demod_ret_val = test_obj.demodulate(self._demod_arg_s)
            mod_ret_val = test_obj.modulate(demod_ret_val)
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

    def set_demodulate_test_input(self, samples: Any, filt: Any) -> None:
        """Sets test case input for the call to the demodulate() method.

        Args:
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
        """
        self._demod_arg_s = samples
        self._demod_arg_f = filt
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
            mapper: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            filt: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self._validate_type(modem_order, 'modem_order', bool)
        self.set_modulate_test_input(bin_bytes=bin_bytes, mapper=mapper)
        self.set_demodulate_test_input(samples=samples, filt=filt)
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

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s01_realistic_usage_mo_dem(self):
        """5.03 Demod 101 FoI 2, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s02_realistic_usage_dem_mo(self):
        """Radio Data System (RDS) inspired settings, dem --> mo order."""
        samp_rate = 57000  # RDS-inspired
        sym_rate = 2375    # RDS-inspired
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.set_test_file_input_return(self.test_bfsk_in2)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s03_realistic_usage_mo_dem(self):
        """5.03 Demod 101 FoI 2, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s04_realistic_usage_dem_mo(self):
        """5.03 Demod 101 FoI 2, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 3 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 3 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.set_test_file_input_return(self.test_bfsk_in3)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s05_real_data_rds_set_msg00_a_mo_dem(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = self.RDS_SET1_MSG00A
        samples = None  # Will be defined by dynamic test case execution
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s06_real_data_rds_set_msg00_a_dem_mo(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s07_real_data_rds_set_msg00_a_mo_dem(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = self.RDS_SET1_MSG00A
        samples = None  # Will be defined by dynamic test case execution
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s08_real_data_rds_set_msg00_a_dem_mo(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s09_real_data_fhss_chan_01_preamble_mo_dem(self):
        """5.05 FHSS Channel 01 Preamble, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = self.FHSS_CHANNEL_01_PREAMBLE
        samples = None  # Will be defined by dynamic test case execution
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s10_real_data_fhss_chan_01_preamble_dem_mo(self):
        """5.05 FHSS Channel 01 Preamble, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s11_real_data_rds_set_msg00_a_with_awgn(self):
        """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A with AWGN (poor SNR)."""
        # BPSKConfig() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        snr_db = self.SNR_POOR
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_noisy_input(samples, snr_db)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s12_real_data_demod_101_foi_1_pdu_with_awgn(self):
        """5.03 Demod 101 FoI 1 PDU with AWGN (poor SNR)."""
        # BPSKConfig() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        snr_db = self.SNR_POOR
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_noisy_input(samples, snr_db)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s13_real_data_fhss_chan_01_preamble_with_awgn(self):
        """5.05 FHSS Channel 01 Preamble with AWGN (poor SNR)."""
        # BPSKConfig() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        snr_db = self.SNR_POOR
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_noisy_input(samples, snr_db)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s14_real_data_demod_101_foi3_mo_dem(self):
        """Demod 101 FoI3, decimated and filtered, mo --> dem order."""
        # BPSKConfig() args
        samp_rate = 240000  # Demod 101 FoI3, decimated
        sym_rate = 600      # Demod 101 FoI3 baud rate
        f0 = -9766 / 2      # Demod 101 FoI3 9.766KHz width
        f1 = 9766 / 2       # Demod 101 FoI3 9.766KHz width
        phase = None
        # modulate()/demodulate() args
        bin_bytes = \
            b'0000000001010101010101010101010101010101110100111001000101010111' \
            b'0110010101101100011000110110111101101101011001010010000001100010' \
            b'0110000101100011011010110010000100100000010101000110100001101001' \
            b'0111001100100000011010010111001100100000010001000110010101101101' \
            b'0110111101100100001000000011000100110000001100010010000001110000' \
            b'0110000101110010011101000010000000110010001011100010000001100110' \
            b'0110110001100001011001110111101101100110011100100011001101110001' \
            b'0111010101000101011011100100001101111001010111110111001101001000' \
            b'0011000101000110001101110101111101101011001100110111100100110001' \
            b'01101110010001110111110100000000'
        samples = None  # Will be defined by dynamic test case execution
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip("TO DO: DON'T DO NOW... Update and define this test case")
    def test_s15_single_byte_alt_bits_dem_mo(self):
        """Demod 101 FoI3, decimated and filtered, dem --> mo order."""
        # BPSKConfig() args
        samp_rate = 240000  # Demod 101 FoI3, decimated
        sym_rate = 600      # Demod 101 FoI3 baud rate
        f0 = -9766 / 2      # Demod 101 FoI3 9.766KHz width
        f1 = 9766 / 2       # Demod 101 FoI3 9.766KHz width
        phase = None
        self.set_bpsk_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.set_test_file_input_return(self.test_bfsk_in4)


if __name__ == '__main__':
    execute_test_cases()
