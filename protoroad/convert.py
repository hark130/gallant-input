"""Convert things into something else."""

# Standard Imports
# Third Party Imports
import numpy as np
# Local Imports


def convert_hex_str_to_binary(hex_str: str) -> bytes:
    """Convert a hex string into binary bytes."""
    return np.array(f"{int(hex_str, 16):08b}", dtype='S8')


def convert_int_to_binary(num: int) -> bytes:
    """Convert an integer to binary bytes."""
    bin_str = f"{num:08b}"
    return bin_str.encode("ascii")
