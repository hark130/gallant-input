"""Functionality to encode and decode data."""

# Standard Imports
import math
# Third Party Imports
import numpy
# Local Imports
from gallant_input.validation import (validate_binary_bytes, validate_float_or_complex,
                                      validate_int, validate_ndarray, validate_pos_int,
                                      validate_type)


def convert_bytes_to_bits(bin_bytes: bytes) -> numpy.ndarray:
    """Convert a bytes object containing binary data to an array object.

    Args:
        bin_bytes: A bytes object containing binary binary to convert.

    Returns:
        The converted bin_bytes value.

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value (e.g., "...and I thought I saw a 2" -Bender).
    """
    # LOCAL VARIABLES
    bit_array = None  # Converted bytes to bit array

    # INPUT VALIDATION
    validate_binary_bytes(validate_this=bin_bytes, param_name='bin_bytes', exact_len=None)

    # CONVERT IT
    bit_array = numpy.unpackbits(numpy.frombuffer(bin_bytes, dtype=numpy.uint8))

    # DONE
    return bit_array


def decode_differential_binary(bin_bytes: bytes) -> bytes:
    """Differential-decode a bytes object containing binary data.

    Args:
        bin_bytes: A bytes object containing binary to differentially-decode.

    Returns:
        The differentially-decoded bin_bytes value.

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value (e.g., "...and I thought I saw a 2" -Bender).
    """
    # LOCAL VARIABLES
    decoded = b''  # Decoded bin_bytes bits

    # INPUT VALIDATION
    validate_binary_bytes(validate_this=bin_bytes, param_name='bin_bytes', exact_len=None)
    if len(bin_bytes) < 2:
        raise ValueError('Unable to differentially decode a bytes object with less than 2 bits')

    # DECODE IT
    decoded = bytes(chr(bin_bytes[0]), 'ascii')
    for prev, cur in zip(bin_bytes, bin_bytes[1:]):
        decoded = decoded + bytes(str(int(chr(prev)) ^ int(chr(cur))), 'ascii')

    # DONE
    return decoded


def map_bits_to_symbols(bitstream: numpy.ndarray, bits_per_symbol: int,
                        mapper: dict[int, float | complex]) -> numpy.ndarray:
    """Map binary data to symbols according to the mapper.

    The number of entries in mapper must equal 2^bits_per_symbol.

    Args:
        bitstream: An array of binary data to map to symbols.
        bits_per_symbol: The number of bits included in each symbol.
        mapper: The bits --> symbol dictionary.

    Returns:
        Any array of symbols mapped according to the mapper dictionary.

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    pad = 0         # The number of bits to pad to bitstream
    grouped = None  # The padded bitstream grouped into bits_per_symbol chunks
    ints = None     # Bits converted to integers
    mapping = None  # Bitstream mapped to mapper values

    # VALIDATION
    validate_ndarray(array=bitstream, array_name='bitstream', can_be_empty=False,
                     num_dim=None, must_be_complex=False)
    _validate_bps_to_mapper(bits_per_symbol, mapper)

    # MAP IT
    # Pad
    pad = (-len(bitstream)) % bits_per_symbol
    if pad:
        bitstream = numpy.concatenate([bitstream, numpy.zeros(pad, dtype=numpy.uint8)])  # Add zeros
    # Reshape
    grouped = bitstream.reshape(-1, bits_per_symbol)
    # Convert bits to integers
    ints = grouped.dot(1 << numpy.arange(bits_per_symbol)[::-1])
    # Map to symbols
    mapping = numpy.array([mapper[i] for i in ints])

    # DONE
    return mapping


def upsample(symbols: numpy.ndarray, samples_per_symbol: int) -> numpy.ndarray:
    """Convert symbols into samples.

    Args:
        symbols: An array of symbols.
        samples_per_symbol: The number of samples required to represent one symbol.

    Returns:
        Each symbol in the symbols array repeated samples_per_symbol number of times.

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    samples = None  # The symbols array, upsampled

    # INPUT VALIDATION
    validate_ndarray(symbols, 'symbols', can_be_empty=False, num_dim=None, must_be_complex=False)
    validate_pos_int(samples_per_symbol, 'samples_per_symbol')

    # UPSAMPLE IT
    samples = numpy.repeat(symbols, samples_per_symbol)

    # DONE
    return samples


def _validate_bps_to_mapper(bits_per_symbol: int, mapper: dict[int, float | complex]) -> None:
    """Validate these arguments under their own strength and against each other."""
    # VALIDATION
    validate_pos_int(bits_per_symbol, 'bits_per_symbol')
    validate_type(mapper, 'mapper', dict)
    if len(mapper) != math.pow(2, bits_per_symbol):
        raise ValueError(f'The length of the "mapper" dictionary ({len(mapper)}) does not equal '
                         f'2^{bits_per_symbol}')
    for key, value in mapper:
        validate_int(key, 'a key in the mapper dictionary')
        if key < 0:
            raise ValueError(f'Keys in the "mapper" dictionary may not be negative: {key}')
        validate_float_or_complex(value, 'a value in the mapper dictionary')
