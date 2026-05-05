"""Defines the base modem.ook OOK() Component Test Class.

Typical Usage:
    python -m test                                      # Run *all* the test cases
    python -m test.comp_test                            # Run *all* the component test cases
    python -m test.comp_test.test_modem                 # Run *all* modem sub-package test cases
    python -m test.comp_test.test_modem.test_modem_ook  # Run *all* OOK test cases
    # Run just this normal 1 unit test
    python -m test.comp_test.test_modem.test_modem_ook -k n01

Environment variable usage:
    # GENERATING REPORT OUTPUT
    > export TEDIOUS_START_VERBOSE_OVERRIDE=True          # Use this to set verbosity to ALL
    > python -m test.comp_test.test_modem.test_modem_ook  # Executes all modem.ook OOK() test cases
    > unset TEDIOUS_START_VERBOSE_OVERRIDE                # Unset it to "clean" your environment
"""

# Standard Imports
from typing import Any
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
import numpy
# Local Imports
from gallant_input.modem.ook import OOK
from test.comp_test.test_modem.modem_comp_test import ModemCompTest
from test.modify import convert_bin_bytes_to_array, upsample_test_input


class OOKModemCompTest(ModemCompTest):
    """GAIN.modem.ook OOK() component test class.

    Defines functionality needed to run component tests on the OOK() modem class.
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """AISUnitTest ctor."""
        # ATTRIBUTES
        self._demod_arg_s = None       # Test case input: OOK().demodulate(samples) arg
        self._demod_arg_t = None       # Test case input: OOK().demodulate(threshold) arg
        self._mod_arg_bb = None        # Test case input: OOK().modulate(bin_bytes) arg
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
            demod_ret_val = test_obj.demodulate(mod_ret_val, self._demod_arg_t)
            test_result = demod_ret_val
        else:
            demod_ret_val = test_obj.demodulate(self._demod_arg_s, self._demod_arg_t)
            mod_ret_val = test_obj.modulate(demod_ret_val)
            test_result = mod_ret_val

        # DONE
        return test_result

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

    # def run_test_exception_input(self, bin_bytes: Any, samples: Any, threshold: Any,
    #                              exception_type: Exception, exception_msg: str,
    #                              modem_order: bool = True) -> None:
    #     """Common method calls for a test case expected to raise an exception.

    #     Test author must first call self.set_modem_ctor_args().

    #     Args:
    #         bin_bytes: Test case input for the modulate method argument of the same name.
    #         samples: Test case input for the demodulate method argument of the same name.
    #         threshold: Test case input for the demodulate method argument of the same name.
    #         exception_type: An Exception type to expect (e.g., ValueError).
    #         exception_msg: A sub-string, empty or not, to look for in the raised Exception.
    #         modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
    #             Othersise, the call order is reversed.
    #     """
    #     self.set_oob_test_input(bin_bytes=bin_bytes, samples=samples, threshold=threshold,
    #                             modem_order=modem_order)
    #     self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
    #     self.run_test()

    def run_test_return_input(self, bin_bytes: Any, samples: Any, threshold: Any,
                              modem_order: bool = True) -> None:
        """Common method calls for a test case expected to return an expected result.

        The expected results depends on modem_order.  Test author must first call
        self.set_modem_ctor_args().

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            threshold: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self.set_test_input_return(bin_bytes=bin_bytes, samples=samples, threshold=threshold,
                                   modem_order=modem_order)
        self.run_test()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def set_demodulate_test_input(self, samples: Any, threshold: Any) -> None:
        """Sets test case input for the call to the demodulate() method.

        Args:
            samples: Test case input for the demodulate method argument of the same name.
            threshold: Test case input for the demodulate method argument of the same name.
        """
        self._demod_arg_s = samples
        self._demod_arg_t = threshold
        self._defined_test_input = True

    def set_modulate_test_input(self, bin_bytes: Any) -> None:
        """Sets test case input for the call to the modulate() method.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
        """
        self._mod_arg_bb = bin_bytes
        self._defined_test_input = True

    def set_oob_test_input(self, bin_bytes: Any, samples: Any, threshold: Any,
                           modem_order: bool = True) -> None:
        """Sets out-of-band test case input for both method calls and sets the test case call order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            threshold: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self._validate_type(modem_order, 'modem_order', bool)
        self.set_modulate_test_input(bin_bytes=bin_bytes)
        self.set_demodulate_test_input(samples=samples, threshold=threshold)
        self._modem_call_order = modem_order

    def set_test_input_return(self, bin_bytes: Any, samples: Any, threshold: Any,
                              modem_order: bool = True) -> None:
        """Sets test case input for both method calls, test case call order, and expected results.

        The expected results depends on modem_order.

        Args:
            bin_bytes: Test case input for the modulate method argument of the same name.
            samples: Test case input for the demodulate method argument of the same name.
            threshold: Test case input for the demodulate method argument of the same name.
            modem_order: [OPTIONAL] If True, the test case will call modulate() then demodulate().
                Othersise, the call order is reversed.
        """
        self.set_oob_test_input(bin_bytes, samples, threshold, modem_order)
        if modem_order:
            self.expect_return(bin_bytes)
        else:
            self.expect_return(samples)  # This may become a problem if ever I add gaussian noise

    def create_test_obj(self) -> OOK:
        """Create an OOK() test object.

        Strongly consider calling self.set_ctor_args() first.
        """
        return OOK(sample_rate=self.input_sample_rate, symbol_rate=self.input_symbol_rate)


class NormalOOKModemCompTest(OOKModemCompTest):
    """Normal Test Cases."""

    def test_n01_single_byte_alt_bits_mo_dem(self):
        """Single byte, alternating bits, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_n02_single_byte_alt_bits_dem_mo(self):
        """Single byte, alternating bits, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_n03_single_byte_alt_bits_mo_dem_valid_threshold(self):
        """Single byte, alternating bits, manual threshold, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_n04_single_byte_alt_bits_dem_mo_valid_threshold(self):
        """Single byte, alternating bits, manual threshold, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_n05_single_byte_all_zeros_mo_dem(self):
        """Single byte, all zeros, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'00000000'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_n06_single_byte_all_zeros_dem_mo(self):
        """Single byte, all zeros, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_ZEROES, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_n07_single_byte_all_zeros_mo_dem_valid_threshold(self):
        """Single byte, all zeros, manual threshold, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'00000000'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_n08_single_byte_all_zeros_dem_mo_valid_threshold(self):
        """Single byte, all zeros, manual threshold, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_ZEROES, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_n09_single_byte_all_ones_mo_dem(self):
        """Single byte, all ones, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'11111111'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_n10_single_byte_all_ones_dem_mo(self):
        """Single byte, all ones, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_ONES, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_n11_single_byte_all_ones_mo_dem_valid_threshold(self):
        """Single byte, all ones, manual threshold, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'11111111'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_n12_single_byte_all_ones_dem_mo_valid_threshold(self):
        """Single byte, all ones, manual threshold, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_ONES, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)


class BoundaryOOKModemCompTest(OOKModemCompTest):
    """Boundary Test Cases."""

    def test_b01_one_bit_on_mo_dem(self):
        """One bit: on, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'1'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b02_one_bit_on_dem_mo(self):
        """One bit: on, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(numpy.resize(self.SAMPLES_ALL_ONES, 1), samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_b03_one_bit_on_mo_dem_valid_threshold(self):
        """One bit: on, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'1'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b04_one_bit_on_dem_mo_valid_threshold(self):
        """One bit: on, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(numpy.resize(self.SAMPLES_ALL_ONES, 1), samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_b05_one_bit_off_mo_dem(self):
        """One bit: off, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'0'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b06_one_bit_off_dem_mo(self):
        """One bit: off, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(numpy.resize(self.SAMPLES_ALL_ZEROES, 1), samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_b07_one_bit_off_mo_dem_valid_threshold(self):
        """One bit: off, mo --> dem order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = b'0'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b08_one_bit_off_dem_mo_valid_threshold(self):
        """One bit: off, dem --> mo order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 80
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(numpy.resize(self.SAMPLES_ALL_ZEROES, 1), samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_b09_lowest_symbol_rate_mo_dem(self):
        """Smallest symbol rate, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b10_lowest_symbol_rate_dem_mo(self):
        """Smallest symbol rate, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_b11_lowest_symbol_rate_mo_dem_valid_threshold(self):
        """Smallest symbol rate, mo --> dem order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b12_lowest_symbol_rate_dem_mo_valid_threshold(self):
        """Smallest symbol rate, dem --> mo order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 4800
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_b13_lowest_samples_per_symbol_mo_dem(self):
        """Smallest samples per symbol, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 1
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b14_lowest_samples_per_symbol_dem_mo(self):
        """Smallest samples per symbol, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 1
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_b15_lowest_samples_per_symbol_mo_dem_valid_threshold(self):
        """Smallest samples per symbol, mo --> dem order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 1
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_b16_lowest_samples_per_symbol_dem_mo_valid_threshold(self):
        """Smallest samples per symbol, dem --> mo order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 1
        sym_rate = 1
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)


class SpecialOOKModemCompTest(OOKModemCompTest):
    """Special Test Cases."""

    def test_s01_realistic_usage_mo_dem(self):
        """5.03 Demod 101 FoI 2, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_s02_realistic_usage_dem_mo(self):
        """5.03 Demod 101 FoI 2, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_s03_realistic_usage_mo_dem_valid_threshold(self):
        """5.03 Demod 101 FoI 2, mo --> dem order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # modulate()/demodulate() args
        bin_bytes = b'10101010'
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_s04_realistic_usage_dem_mo_valid_threshold(self):
        """5.03 Demod 101 FoI 2, dem --> mo order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 480000  # 5.03 Demod 101 FoI 2 sample rate
        sym_rate = 800      # 5.03 Demod 101 FoI 2 symbol rate
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = create_test_samples(self.SAMPLES_ALL_10S, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_s05_real_data_rds_set_msg00_a_mo_dem(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # modulate()/demodulate() args
        bin_bytes = self.RDS_SET1_MSG00A
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_s06_real_data_rds_set_msg00_a_dem_mo(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = convert_bin_bytes_to_array(self.RDS_SET1_MSG00A, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_s07_real_data_rds_set_msg00_a_mo_dem_valid_threshold(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, mo --> dem order, valid thresh."""
        # Modem.__init__() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # modulate()/demodulate() args
        bin_bytes = self.RDS_SET1_MSG00A
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_s08_real_data_rds_set_msg00_a_dem_mo_valid_threshold(self):
        """RDS SET 1: KONO 101.1 FM Group Type 00A, dem --> mo order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
        sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = convert_bin_bytes_to_array(self.RDS_SET1_MSG00A, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_s09_real_data_fhss_chan_01_preamble_mo_dem(self):
        """5.05 FHSS Channel 01 Preamble, mo --> dem order."""
        # Modem.__init__() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # modulate()/demodulate() args
        bin_bytes = self.FHSS_CHANNEL_01_PREAMBLE
        samples = None  # Will be defined by dynamic test case execution
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_s10_real_data_fhss_chan_01_preamble_dem_mo(self):
        """5.05 FHSS Channel 01 Preamble, dem --> mo order."""
        # Modem.__init__() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = convert_bin_bytes_to_array(self.FHSS_CHANNEL_01_PREAMBLE, samp_rate, sym_rate)
        threshold = None  # Automatically determine the threshold
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    def test_s11_real_data_fhss_chan_01_preamble_mo_dem_valid_threshold(self):
        """5.05 FHSS Channel 01 Preamble, mo --> dem order, valid thresh."""
        # Modem.__init__() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # modulate()/demodulate() args
        bin_bytes = self.FHSS_CHANNEL_01_PREAMBLE
        samples = None  # Will be defined by dynamic test case execution
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=True)

    def test_s12_real_data_fhss_chan_01_preamble_dem_mo_valid_threshold(self):
        """5.05 FHSS Channel 01 Preamble, dem --> mo order, valid threshold."""
        # Modem.__init__() args
        samp_rate = 26000000  # 5.05 FHSS sample rate
        sym_rate = 250000     # 5.05 FHSS symbol rate
        # modulate()/demodulate() args
        bin_bytes = None  # Will be defined by dynamic test case execution
        samples = convert_bin_bytes_to_array(self.FHSS_CHANNEL_01_PREAMBLE, samp_rate, sym_rate)
        threshold = 0.5
        self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
        self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    # def test_s13_real_data_rds_set_msg00_a_with_awgn(self):
    #     """RDS SET 1: KONO 101.1 FM Live Capture of Group Type 00A with AWGN (poor SNR)."""
    #     # Modem.__init__() args
    #     samp_rate = 57000  # RDS is sampled at 57 kHz to allow for integer-based processing
    #     sym_rate = 2375    # Twice the bit rate of 1187.5 bits per second (bps)
    #     # modulate()/demodulate() args
    #     bin_bytes = None  # Will be defined by dynamic test case execution
    #     samples = convert_bin_bytes_to_array(self.RDS_SET1_MSG00A, samp_rate, sym_rate)
    #     threshold = 0.5
    #     self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
    #     self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    # def test_s14_real_data_demod_101_foi_1_pdu_with_awgn(self):
    #     """5.03 Demod 101 FoI 1 PDU with AWGN (poor SNR)."""
    #     # Modem.__init__() args
    #     samp_rate = 480000  # 5.03 Demod 101 FoI 1 sample rate
    #     sym_rate = 800      # 5.03 Demod 101 FoI 1 symbol rate
    #     # modulate()/demodulate() args
    #     bin_bytes = None  # Will be defined by dynamic test case execution
    #     samples = convert_bin_bytes_to_array(self.DEMOD_101_FOI_1_PDU, samp_rate, sym_rate)
    #     threshold = 0.5
    #     self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
    #     self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)

    # def test_s15_real_data_fhss_chan_01_preamble_with_awgn(self):
    #     """5.05 FHSS Channel 01 Preamble with AWGN (poor SNR)."""
    #     # Modem.__init__() args
    #     samp_rate = 26000000  # 5.05 FHSS sample rate
    #     sym_rate = 250000     # 5.05 FHSS symbol rate
    #     # modulate()/demodulate() args
    #     bin_bytes = None  # Will be defined by dynamic test case execution
    #     samples = convert_bin_bytes_to_array(self.FHSS_CHANNEL_01_PREAMBLE, samp_rate, sym_rate)
    #     threshold = 0.5
    #     self.set_modem_ctor_args(sample_rate=samp_rate, symbol_rate=sym_rate)
    #     self.run_test_return_input(bin_bytes, samples, threshold, modem_order=False)


def create_test_samples(samples: numpy.ndarray, sample_rate: float | int,
                        symbol_rate: float | int) -> numpy.ndarray:
    """Create a valid 'samples' array, using production code, for use as test case input."""
    return upsample_test_input(samples=samples, sample_rate=sample_rate, symbol_rate=symbol_rate)


if __name__ == '__main__':
    execute_test_cases()
