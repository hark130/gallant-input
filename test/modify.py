"""This module defines common-use functionality to modify test input/create expected output."""

# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, upsample
from gallant_input.modem.calc import calculate_sps


def convert_bin_bytes_to_array(bin_bytes: bytes, sample_rate: int | float,
                               symbol_rate: int | float) -> numpy.ndarray:
    """Convert a binary bytes object to an array."""
    # LOCAL VARIABLES
    sps = int(sample_rate // symbol_rate)  # Samples per symbol
    samples = None                         # An array of the sample values
    array = None                           # The numpy.ndarray formed from the samples

    # COMPUTE IT
    samples = []
    for bin_byte in bin_bytes:
        samples += [int(chr(bin_byte))] * sps
    samples = b''.join([bytes(str(sample), 'ascii') for sample in samples])
    array = convert_ascii_bin_bytes_to_bits(samples).astype(numpy.complex64)

    # DONE
    return array


def upsample_test_input(samples: numpy.ndarray, sample_rate: float | int,
                        symbol_rate: float | int) -> numpy.ndarray:
    """Create test case input by upsampling a valid 'samples' array, using production code."""
    return upsample(symbols=samples, samples_per_symbol=calculate_sps(sample_rate, symbol_rate))
