"""This module defines common-use functionality to modify test input/create expected output."""

# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, upsample
from gallant_input.modem.calc import calculate_sps
from gallant_input.validation import validate_int_or_float, validate_ndarray


def add_awgn(samples: numpy.ndarray, snr_db: float | int) -> numpy.ndarray:
    """Add AWGN to samples, regardless of dtype, based on desired SNR.

    Additive White Gaussian Noise (AWGN)
    Signal-to-Noise Ratio (SNR)

    Args:
        samples: The original samples to add AWGN to.
        snr_db: The desigred SNR, in decibels.

    Returns:
        A noisy signal, derived from samples, in an ndarray.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    rng = numpy.random.default_rng()  # Random noise generator object
    new_samps = None                  # A copy of samples as complex128 samples
    signal_power = None               # Original signal power
    snr_linear = None                 # Desired noise power
    noise_power = None                # Solve for P(noise)
    sigma = None                      # Standard deviation of the noise
    noise = None                      # Randomly generated AWGN
    noisy = None                      # Noise + samples

    # INPUT VALIDATION
    validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                   must_be_complex=False)
    validate_int_or_float(snr_db, 'snr_db')  # Ignore actual value since it could be anything

    # ADD IT
    new_samps = samples.astype(numpy.complex128)
    signal_power = numpy.mean(numpy.abs(new_samps) ** 2)
    if signal_power <= 0:
        noise_power = 1e-3  # Arbitrary noise floor for a non-existent signal
    else:
        snr_linear = 10 ** (snr_db / 10)
        noise_power = signal_power / snr_linear
    sigma = numpy.sqrt(noise_power / 2)
    noise = rng.normal(0, sigma, samples.shape) + 1j * rng.normal(0, sigma, samples.shape)
    noisy = samples + noise

    # DONE
    return noisy.astype(samples.dtype)  # Cast back to original dtype


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
