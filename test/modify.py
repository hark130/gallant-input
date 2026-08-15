"""This module defines common-use functionality to modify test input/create expected output."""

# Standard Imports
import random
# Third Party Imports
import numpy
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, upsample
from gallant_input.modem.calc import calculate_sps
from gallant_input.validation import (validate_float, validate_int_or_float, validate_mapper,
                                      validate_ndarray, validate_pos_int, validate_type)


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


def change_sample_phase(sample: complex, delta_phase: float) -> complex:
    """Change the sample's phase by delta_phase.

    Negative values will decrease the phase.  A delta_phase of zero will result in no change.
    """
    # INPUT VALIDATION
    validate_type(sample, 'sample', complex)
    validate_float(delta_phase, 'delta_phase')

    # DONE
    return sample * numpy.exp(1j * delta_phase)


def convert_bin_bytes_to_bpsk(bin_bytes: bytes, sample_rate: int | float, symbol_rate: int | float,
                              bit_map: dict[int, complex]) -> numpy.ndarray:
    """Convert a binary bytes object to a BPSK array given a mapping dictionary."""
    # LOCAL VARIABLES
    sps = int(sample_rate // symbol_rate)  # Samples per symbol
    samples = None                         # An array of the sample values
    array = None                           # The numpy.ndarray formed from the samples

    # INPUT VALIDATION
    validate_mapper(bit_map, 'bit_map', bits_per_symbol=1)  # B is for Binary

    # COMPUTE IT
    samples = []
    for bin_byte in bin_bytes:
        samples += [int(chr(bin_byte))] * sps
    array = numpy.array([bit_map[sample] for sample in samples], dtype=numpy.complex64)

    # DONE
    return array


def convert_bin_bytes_to_ook(bin_bytes: bytes, sample_rate: int | float,
                             symbol_rate: int | float) -> numpy.ndarray:
    """Convert a binary bytes object to an OOK array."""
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


def convert_bin_bytes_to_qpsk(bin_bytes: bytes, sample_rate: int | float, symbol_rate: int | float,
                              bit_map: dict[int, complex]) -> numpy.ndarray:
    """Convert a binary bytes object to a QPSK array given a mapping dictionary.


    If the length of bin_bytes does not conform to the implied bit mapping
    (e.g., len(bin_bytes) % bits-per-symbol != 0) then bin_bytes will be padded with trailing zeros.

    Args:
        bin_bytes: The binary, as a bytes object, to map to complex samples.
        sample_rate: The number of samples of a continuous-time signal that are recorded
            (or generated) per second.
        symbol_rate: The number of symbols-per-second (AKA baud rate).
        bit_map: The mapping of bits to complex samples.
    """
    # LOCAL VARIABLES
    sps = int(sample_rate // symbol_rate)  # Samples per symbol
    bps = 2                                # Bits-per-symbol
    samples = None                         # An array of the sample values
    array = None                           # The numpy.ndarray formed from the samples

    # INPUT VALIDATION
    validate_mapper(bit_map, 'bit_map', bits_per_symbol=bps)  # QPSK == 4PSK == 2^2PSK

    # PREPARE
    bin_bytes = pad_bin_bytes(bin_bytes, bps)

    # COMPUTE IT
    samples = []
    for bin_chunk in [bin_bytes[index:index+bps] for index in range(0, len(bin_bytes), bps)]:
        samples += [int(bin_chunk, 2)] * sps
    array = numpy.array([bit_map[sample] for sample in samples], dtype=numpy.complex64)

    # DONE
    return array


def generate_bin_bytes(num_bits: int) -> bytes:
    """Generate a random binary string as ASCII bytes.

    Args:
        num_bits: Number of random bits to generate.

    Returns:
        A bytes object containing ASCII '0' and '1' characters.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    validate_pos_int(num_bits, 'num_bits')
    return f'{random.getrandbits(num_bits):0{num_bits}b}'.encode('ascii')


def pad_bin_bytes(original: bytes, bits_per_symbol: int) -> bytes:
    """Pad a bin bytes object with zeros to match a given bits_per_symbol."""
    padded = original
    while len(padded) % bits_per_symbol != 0:
        padded = padded + b'0'
    return padded


def rotate_mapping(mapping: dict[int, complex], delta_phase: float) -> dict[int, complex]:
    """Rotate the phase of every value in mapping by delta_phase, preserving the keys.

    Example:
        rotate_mapping({0: -1+0j, 1: 1+0j}, 0.0)          ≈ {0: -1+0j, 1: 1+0j}  # No change
        rotate_mapping({0: -1+0j, 1: 1+0j}, numpy.pi / 2) ≈ {0: 0-1j, 1: 0+1j}   # Rotated 90°
        rotate_mapping({0: -1+0j, 1: 1+0j}, numpy.pi)     ≈ {0: 1+0j, 1: -1+0j}  # Rotated 180°
        rotate_mapping({0: -1+0j, 1: 1+0j}, 2 * numpy.pi) ≈ {0: -1+0j, 1: 1+0j}  # No change
    """
    # LOCAL VARIABLES
    new_map = {}  # Rotated mapping

    # INPUT VALIDATION
    validate_type(mapping, 'mapping', dict)

    # ROTATE IT
    for key, val in mapping.items():
        new_map[key] = change_sample_phase(sample=val, delta_phase=delta_phase)

    # DONE
    return new_map


def upsample_test_input(samples: numpy.ndarray, sample_rate: float | int,
                        symbol_rate: float | int) -> numpy.ndarray:
    """Create test case input by upsampling a valid 'samples' array, using production code."""
    return upsample(symbols=samples, samples_per_symbol=calculate_sps(sample_rate, symbol_rate))
