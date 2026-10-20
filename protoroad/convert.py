"""Convert things into something else."""

# Standard Imports
# Third Party Imports
import numpy as np
# Local Imports


def convert_bin_bytes_to_ascii(binary: bytes) -> bytes:
    """Convert a bytes-representation of a binary number to an ASCII string.

    Example Usage:
        convert_bin_bytes_to_ascii(b'01010111011010000110111100111111') -> b'Who?'

    Args:
        binary: A binary literal in a bytes object.

    Returns:
        The binary values converted to ASCII, as a byte string.

    Raises:
        TypeError: Invalid data type.
        ValueError: The bytes object contains non-binary characters.
    """
    bits = np.frombuffer(binary, dtype=np.uint8) - ord("0")
    string = np.packbits(bits).tobytes()
    return string


def convert_bit_array_to_ascii(bits: np.ndarray) -> bytes:
    """Converts demodulated samples to an ASCII string.

    Example Usage:
        convert_bit_array_to_ascii(np.ndarray([0,0,1,1,1,1,1,1], dtype=np.uint8) -> b'?'
    """
    binary = convert_bit_array_to_bytes(bits=bits)
    string = convert_bin_bytes_to_ascii(binary=binary)
    return string


def convert_bit_array_to_bytes(bits: np.ndarray) -> bytes:
    """Convert demodulated samples to a bytes object."""
    return (np.asarray(bits, dtype=np.uint8) + ord("0")).tobytes()


def convert_hex_str_to_binary(hex_str: str) -> bytes:
    """Convert a hex string into binary bytes."""
    return np.array(f"{int(hex_str, 16):08b}", dtype="S8")


def convert_msg_to_binary(message: bytes) -> bytes:
    """Convert an ASCII byte string to binary bytes."""
    return ''.join(f'{byte:08b}' for byte in message).encode("ascii")


def convert_int_to_binary(num: int) -> bytes:
    """Convert an integer to binary bytes."""
    bin_str = f"{num:08b}"
    return bin_str.encode("ascii")
