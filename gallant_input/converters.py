"""Defines all of the convert_x_to_y() GAIN functions."""

# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.validation import (validate_binary_bytes, validate_bool, validate_bytes_or_str,
                                      validate_int, validate_string)


def convert_ascii_to_bin_bytes(message: str, clean_it: bool = False) -> bytes:
    """Convert an ASCII message to padded binary bytes.

    Args:
        message: An ASCII message
        clean_it: [OPTIONAL] Remove characters that aren't: printable ASCII, tabs, newlines.

    Returns:
        The binary version of the message.

    Raises:
        TypeError: Invalid data type.
    """
    validate_string(message, 'message', can_be_empty=False)
    validate_bool(clean_it, 'clean_it')
    if clean_it:
        message = sanitize_ascii(message)
    return ''.join(f'{ord(char):08b}' for char in message).encode()


def convert_bin_bytes_to_ascii(binary: bytes, clean_it: bool = False) -> str:
    """Convert a bytes-representation of a binary number to an ASCII string.

    Example Usage:
        convert_bin_bytes_to_ascii(b'01010111011010000110111100111111') -> 'Who?'

    Args:
        binary: A binary literal in a bytes object.
        clean_it: [OPTIONAL] Remove characters that aren't: printable ASCII, tabs, newlines.

    Returns:
        The binary values converted to ASCII, as a string.

    Raises:
        TypeError: Invalid data type.
        ValueError: The bytes object contains non-binary characters.
    """
    validate_binary_bytes(validate_this=binary, param_name='binary', exact_len=None)
    validate_bool(clean_it, 'clean_it')
    string = ''.join(chr(int(binary[i:i+8], 2)) for i in range(0, len(binary), 8))
    if clean_it:
        string = sanitize_ascii(string)
    return string


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
    validate_binary_bytes(validate_this=binary, param_name='binary', exact_len=None)
    if not binary:
        raise ValueError('The "binary" argument may not be empty')
    return int(binary.decode('ascii'), 2)


def convert_bin_bytes_to_ndarray(binary: bytes, bipolar: bool = False) -> numpy.ndarray:
    """Convert binary bytes to an ndarray.

    Args:
        binary: A binary literal in a bytes object.
        bipolar: [OPTIONAL] If True, the array will be made bipolar (e.g., for better correlation)

    Returns:
        The binary values converted to an numpy.ndarray of dtype numpy.int8.

    Raises:
        TypeError: Invalid data type.
        ValueError: The bytes object contains non-binary characters.
    """
    # LOCAL VARIABLES
    bits = None  # The ndarray

    # VALIDATION
    validate_binary_bytes(binary, 'binary', exact_len=None)
    validate_bool(bipolar, 'bipolar')

    # CONVERT IT
    bits = (numpy.frombuffer(binary, dtype=numpy.uint8) == ord('1')).astype(numpy.int8)
    # Bipolar?
    if bipolar is True:
        return bits * 2 - 1

    # DONE
    return bits


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


def sanitize_ascii(text: bytes | str, replace: bytes | str = b'.') -> bytes | str:
    """Preserves printable ASCII, tabs, and newlines.

    Args:
        text: ASCII text to sanitize.
        replace: [OPTIONAL] The character to replace characters with.  This character may be empty.
            This will be converted to the right type prior to replacements.

    Raises:
        TypeError: Invalid data type.
        RuntimeError: Edge case exception if, somehow, text passes validation.

    Returns:
        Sanitized copy of text with the data type preserved.
    """
    # LOCAL VARIABLES
    sanitized = None    # A sanitized version of text to return
    new_char = replace  # Local modified copy of the replacement character

    # INPUT VALIDATION
    validate_bytes_or_str(text, 'text')
    validate_bytes_or_str(replace, 'replace')

    # SANITIZE IT
    if isinstance(text, bytes):
        if not isinstance(new_char, bytes):
            new_char = new_char.encode('ascii')
        sanitized = b''.join(char if char.isprintable() or char in b'\t\n' else new_char
                             for char in text)
    elif isinstance(text, str):
        if not isinstance(new_char, str):
            new_char = new_char.decode('ascii')
        sanitized = ''.join(char if char.isprintable() or char in '\t\n' else new_char
                            for char in text)
    else:
        raise RuntimeError(f'How did we get here?! The "text" parameter is of type "{type(text)}".')

    # DONE
    return sanitized
