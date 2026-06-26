"""Defines all of the convert_x_to_y() GAIN functions."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.validation import validate_bytes, validate_int


def convert_bin_bytes_to_int(binary: bytes) -> int:
    """Convert a bytes-representation of a binary number to an integer.

    Args:
        binary: A binary literal in a bytes object.

    Returns:
        The integer value of the binary.

    Raises:
        TypeError: Invalid data type.
        ValueError: The bytes object contains non-binary characters.
    """
    validate_bytes(validate_this=binary, param_name='binary', exact_len=None)
    if not binary:
        raise ValueError('The "binary" argument may not be empty')
    if not all(bin_chars in b'01' for bin_chars in binary):
        raise ValueError(f'The "binary" argument contains non-binary values: {binary}')
    return int(binary.decode('ascii'), 2)


def convert_bin_bytes_to_hex_str(binary: bytes, add_prefix: bool = True) -> str:
    """Convert a bytes-representation of a binary number to a hex value in a string.

    Example Usage:
        convert_bin_bytes_to_hex_str(b'10101010', True)  -> 0xAA
        convert_bin_bytes_to_hex_str(b'01010101', False) -> 0x55

    Args:
        binary: A binary literal in a bytes object.
        add_prefix: [OPTIONAL] If True, prepend the string with the '0x' prefix.

    Returns:
        The hexadecimal version of the binary value, as a string.

    Raises:
        TypeError: Invalid data type.
        ValueError: The bytes object contains non-binary characters.
    """
    # LOCAL VARIABLES
    bin_int = convert_bin_bytes_to_int(binary=binary)
    bin_hex = f'{bin_int:02X}'

    # ADD PREFIX?
    if add_prefix is True:
        bin_hex = '0x' + bin_hex

    # DONE
    return bin_hex


def convert_bin_bytes_to_ascii(binary: bytes) -> str:
    """Convert a bytes-representation of a binary number to an ASCII string.

    Example Usage:
        convert_bin_bytes_to_ascii(b'01010111011010000110111100111111') -> 'Who?'

    Args:
        binary: A binary literal in a bytes object.

    Returns:
        The binary values converted to ASCII, as a string.

    Raises:
        TypeError: Invalid data type.
        ValueError: The bytes object contains non-binary characters.
    """
    validate_bytes(validate_this=binary, param_name='binary', exact_len=None)
    string = ''.join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8))
    return string


def convert_int_to_bin_bytes(number: int, min_width: int = 8) -> bytes:
    """Convert an integer to its binary value in a bytes object.

    Args:
        number: A value to convert to binary.
        min_width: [OPTIONAL] Minimum width of the bytes object (filled with leading zeros).

    Returns:
        A bytes object containing the binary representation of the number.

    Raises:
        TypeError: Invalid data type.
        ValueError: Invalid value (e.g., min_width may not be negative).
    """
    validate_int(number, 'number')
    validate_int(min_width, 'min_width')
    if min_width < 0:
        raise ValueError(f'Invalid value for "min_width": {min_width}')
    return format(number, f'0{str(min_width)}b').encode('ascii')
