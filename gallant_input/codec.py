"""Functionaly to encode and decode data."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.validation import validate_binary_bytes


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
