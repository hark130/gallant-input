"""Defines the base modem.fsk2 FSK2() Component Test Class.

Typical Usage:
    python -m test                                       # Run *all* the test cases
    python -m test.comp_test                             # Run *all* the component test cases
    python -m test.comp_test.test_modem                  # Run *all* modem sub-package test cases
    python -m test.comp_test.test_modem.test_modem_fsk2  # Run *all* FSK2 test cases
    # Run just this normal 1 unit test
    python -m test.comp_test.test_modem.test_modem_fsk2 -k n01
"""

# Standard Imports
from typing import Any
from unittest import skip
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from test.comp_test.test_modem.modem_comp_test import ModemCompTest
from test.modify import add_awgn, convert_bin_bytes_to_array, upsample_test_input


class FSK2ModemCompTest(ModemCompTest):
    """GAIN.modem.fsk2 FSK2() component test class.

    Defines functionality needed to run component tests on the FSK2() modem class.
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """AISUnitTest ctor."""
        # ATTRIBUTES
        self.input_freq0 = None        # Test case input: freq0
        self.input_freq1 = None        # Test case input: freq1
        self.input_phase = None        # Test case input: phase
        self._demod = False            # Default mod/demod test state
        self._demod_arg_s = None       # Test case input: FSK2().demodulate(samples) arg
        self._mod_arg_bb = None        # Test case input: FSK2().modulate(bin_bytes) arg
        self._modem_call_order = True  # Call order for the two methods: If True, mo --> dem

        super().__init__(*args, **kwargs)

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

# Leave me be, Pylint
# pylint: disable = too-many-arguments, too-many-positional-arguments
    def set_fsk2_ctor_args(self, sample_rate: Any, symbol_rate: Any, freq0: Any, freq1: Any,
                           phase: Any) -> None:
        """Sets the FSK2() argument values in the test class."""
        self.set_modem_ctor_args(sample_rate=sample_rate, symbol_rate=symbol_rate)
        self.input_freq0 = freq0
        self.input_freq1 = freq1
        self.input_phase = phase
# pylint: enable = too-many-arguments, too-many-positional-arguments

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

    def run_test_return_input(self, bin_bytes: Any, samples: Any, modem_order: bool = True) -> None:
        """Common method calls for a test case expected to return an expected result.

        The expected results depends on modem_order.  Test author must first call
        self.set_modem_ctor_args().

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples, modem_order=modem_order)
        self.run_test()

    def run_test_return_noisy_input(self, samples: Any, snr_db: float | int) -> None:
        """Common method for a test case expected to return an expected result on noisy input.

        The expected results depends on modem_order.  Test author must first call
        self.set_modem_ctor_args().  The modem order will always be False and bin_bytes will
        be None (or else, why create noisy samples just to ignore them?).

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            snr_db: The desigred SNR, in decibels, to add to samples.
        """
        noisy = add_awgn(samples, snr_db)
        self.set_test_input_return(bin_bytes=None, samples=noisy,
                                   modem_order=False, skip_exp_ret=True)
        self.expect_return(samples)
        self.run_test()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def set_demodulate_test_input(self, samples: Any) -> None:
        """Sets test case input for the call to the demodulate() method.

        Args:
            samples: Test case input for the demodulate method argument of the same name.
        """
        self._demod_arg_s = samples
        self._defined_test_input = True

    def set_modulate_test_input(self, bin_bytes: Any) -> None:
        """Sets test case input for the call to the modulate() method.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
        """
        self._mod_arg_bb = bin_bytes
        self._defined_test_input = True

    def set_oob_test_input(self, bin_bytes: Any, samples: Any, modem_order: bool = True) -> None:
        """Sets out-of-band test case input for both method calls and sets the test case call order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self._validate_type(modem_order, 'modem_order', bool)
        self.set_modulate_test_input(bin_bytes=bin_bytes)
        self.set_demodulate_test_input(samples=samples)
        self._modem_call_order = modem_order

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def set_test_input_return(self, bin_bytes: Any, samples: Any,
                              modem_order: bool = True, skip_exp_ret: bool = False) -> None:
        """Sets test case input for both method calls, test case call order, and expected results.

        The expected results depends on modem_order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
            skip_exp_ret: [OPTIONAL] If True, the test author must call self.expect_return().
        """
        self.set_oob_test_input(bin_bytes, samples, modem_order)
        if not skip_exp_ret:
            if modem_order:
                self.expect_return(bin_bytes)
            else:
                self.expect_return(samples)
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def create_test_obj(self) -> FSK2:
        """Create an FSK2() test object.

        Strongly consider calling self.set_modem_ctor_args() and self.set_fsk2_ctor_args() first.
        """
        config = None  # FSK2() ctor argument
        self._validate_type(self._demod, '_demod instance attribute', bool)
        config = FSK2Config(sample_rate=self.input_sample_rate,
                            symbol_rate=self.input_symbol_rate,
                            freq0=self.input_freq0, freq1=self.input_freq1,
                            phase=self.input_phase)
        config.set_demod(demod=self._demod)
        return FSK2(config=config)


class NormalFSK2ModemCompTest(FSK2ModemCompTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits_mo_dem(self):
        """Single byte, alternating bits, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_n02_single_byte_alt_bits_dem_mo(self):
        """Single byte, alternating bits, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_n03_single_byte_alt_bits_mo_dem_valid_threshold(self):
        """Single byte, alternating bits, manual threshold, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_n04_single_byte_alt_bits_dem_mo_valid_threshold(self):
        """Single byte, alternating bits, manual threshold, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_n05_single_byte_all_zeros_mo_dem(self):
        """Single byte, all zeros, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'00000000'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_n06_single_byte_all_zeros_dem_mo(self):
        """Single byte, all zeros, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_n07_single_byte_all_zeros_mo_dem_valid_threshold(self):
        """Single byte, all zeros, manual threshold, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'00000000'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_n08_single_byte_all_zeros_dem_mo_valid_threshold(self):
        """Single byte, all zeros, manual threshold, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_n09_single_byte_all_ones_mo_dem(self):
        """Single byte, all ones, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'11111111'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_n10_single_byte_all_ones_dem_mo(self):
        """Single byte, all ones, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_n11_single_byte_all_ones_mo_dem_valid_threshold(self):
        """Single byte, all ones, manual threshold, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'11111111'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_n12_single_byte_all_ones_dem_mo_valid_threshold(self):
        """Single byte, all ones, manual threshold, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)


class BoundaryFSK2ModemCompTest(FSK2ModemCompTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_on_mo_dem(self):
        """One bit: on, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'1'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_b02_one_bit_on_dem_mo(self):
        """One bit: on, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_b03_one_bit_on_mo_dem_valid_threshold(self):
        """One bit: on, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'1'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_b04_one_bit_on_dem_mo_valid_threshold(self):
        """One bit: on, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_b05_one_bit_off_mo_dem(self):
        """One bit: off, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'0'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_b06_one_bit_off_dem_mo(self):
        """One bit: off, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_b07_one_bit_off_mo_dem_valid_threshold(self):
        """One bit: off, mo --> dem order, valid threshold."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'0'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_b08_one_bit_off_dem_mo_valid_threshold(self):
        """One bit: off, dem --> mo order, valid threshold."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 80
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_b09_lowest_symbol_rate_mo_dem(self):
        """Smallest symbol rate, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_b10_lowest_symbol_rate_dem_mo(self):
        """Smallest symbol rate, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_b11_lowest_symbol_rate_mo_dem_valid_threshold(self):
        """Smallest symbol rate, mo --> dem order, valid threshold."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_b12_lowest_symbol_rate_dem_mo_valid_threshold(self):
        """Smallest symbol rate, dem --> mo order, valid threshold."""
        # FSK2Config() args
        samp_rate = 4800
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_b13_samples_per_symbol_too_small_mo_dem(self):
        """Samples per symbol too small, mo --> dem order.

        This is a symbol synchronization issue.
        """
        # FSK2Config() args
        samp_rate = 1
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.set_test_input_return(bin_bytes, samples, modem_order=True, skip_exp_ret=True)
        self.expect_return(b'11010101')
        self.run_test()

    @skip('This test case needs some actual modulated samples')
    def test_b14_samples_per_symbol_too_small_dem_mo(self):
        """Samples per symbol too small, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 1
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_b15_samples_per_symbol_smallest_mo_dem(self):
        """Samples per symbol smallest value to be successful, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 3
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_b16_samples_per_symbol_smallest_dem_mo(self):
        """Samples per symbol smallest value to be successful, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 3
        sym_rate = 1
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)


class SpecialFSK2ModemCompTest(FSK2ModemCompTest):
    """Special Test Cases."""

    def test_s01_realistic_usage_mo_dem(self):
        """5.03 Demod 101 FoI 2, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_s02_realistic_usage_dem_mo(self):
        """5.03 Demod 101 FoI 2, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_s03_realistic_usage_mo_dem(self):
        """5.03 Demod 101 FoI 2, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_s04_realistic_usage_dem_mo(self):
        """5.03 Demod 101 FoI 2, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_s05_real_data_rds_set_msg00_a_mo_dem(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = self.RDS_SET1_MSG00A
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_s06_real_data_rds_set_msg00_a_dem_mo(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_s07_real_data_rds_set_msg00_a_mo_dem(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = self.RDS_SET1_MSG00A
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_s08_real_data_rds_set_msg00_a_dem_mo(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_s09_real_data_fhss_chan_01_preamble_mo_dem(self):
        """5.05 FHSS Channel 01 Preamble, mo --> dem order."""
        # FSK2Config() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = self.FHSS_CHANNEL_01_PREAMBLE
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_s10_real_data_fhss_chan_01_preamble_dem_mo(self):
        """5.05 FHSS Channel 01 Preamble, dem --> mo order."""
        # FSK2Config() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    def test_s11_real_data_fhss_chan_01_preamble_mo_dem_valid_threshold(self):
        """5.05 FHSS Channel 01 Preamble, mo --> dem order, valid thresh."""
        # FSK2Config() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = self.FHSS_CHANNEL_01_PREAMBLE
        samples = None  # Will be defined by dynamic test case execution
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=True)

    @skip('This test case needs some actual modulated samples')
    def test_s12_real_data_fhss_chan_01_preamble_dem_mo_valid_threshold(self):
        """5.05 FHSS Channel 01 Preamble, dem --> mo order, valid threshold."""
        # FSK2Config() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_input(bin_bytes, samples, modem_order=False)

    @skip('This test case needs some actual modulated samples')
    def test_s13_real_data_rds_set_msg00_a_with_awgn(self):
        """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A with AWGN (poor SNR)."""
        # FSK2Config() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        snr_db = self.SNR_POOR
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_noisy_input(samples, snr_db)

    @skip('This test case needs some actual modulated samples')
    def test_s14_real_data_demod_101_foi_1_pdu_with_awgn(self):
        """5.03 Demod 101 FoI 1 PDU with AWGN (poor SNR)."""
        # FSK2Config() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        snr_db = self.SNR_POOR
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_noisy_input(samples, snr_db)

    @skip('This test case needs some actual modulated samples')
    def test_s15_real_data_fhss_chan_01_preamble_with_awgn(self):
        """5.05 FHSS Channel 01 Preamble with AWGN (poor SNR)."""
        # FSK2Config() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        f0 = -sym_rate / 2
        f1 = sym_rate / 2
        phase = None
        # modulate()/demodulate() args
        samples = "TO DO: DON'T DO NOW... Find some actual BFSK samples"
        snr_db = self.SNR_POOR
        self.set_fsk2_ctor_args(samp_rate, sym_rate, f0, f1, phase)
        self.run_test_return_noisy_input(samples, snr_db)


if __name__ == '__main__':
    execute_test_cases()
