"""Functionality to easily build up SigMF metadata."""

# Standard Imports
# Third Party Imports
import sigmf
# Local Imports
from gallant_input.sigmfdatatype import SigMFDataType
from gallant_input.validation import validate_bool, validate_int, validate_type


def build_global_object() -> dict[str:str]:
    """Build a SigMF global object dictionary.

    See: https://sigmf.org/#subsec:GlobalObject

    
    """


def build_dataset_format(is_complex: bool = True, data_type: SigMFDataType = SigMFDataType.FLOAT,
                         bit_width: int = 32, little_e: bool = True) -> str:
    """Build a SigMF Dataset Format that conforms with Augmented Backus-Naur form (ABNF) rules.

    Only IEEE-754 single-precision and double-precision floating-point types are supported by
    the SigMF Core namespace. Note that complex data types are specified by the bit width of
    the individual I/Q components, and not by the total complex pair bitwidth (like Numpy).

    Args:
        is_complex: [OPTIONAL] If True, 'c'.  Otherise it's real: 'r'.
        data_type: [OPTIONAL] SigMFDataType int enum indicating the dataset format data type.
        bit_width: [OPTIONAL] The number of bits in each sample.  Supported values: 8, 16, 32, 64.
        little_e: [OPTIONAL] If True, '_le' for little-endian.  Otherwise it's '_be' for big-endian.
            This argument is ignored if num_bits is 8.

    Returns:
        An ABNF-compliant dataset value.  Default return value is 'cf32_le'.

    Raises:
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES
    valid_widths = [8, 16, 32, 64]  # Supported bit widths
    data_format = ''                # ABNF-compliant SigMF Dataset Format

    # INPUT VALIDATION
    validate_bool(is_complex, 'is_complex')
    validate_type(data_type, 'data_type', SigMFDataType)
    validate_int(bit_width, 'bit_width')
    if bit_width not in valid_widths:
        raise ValueError(f'The "bit_width" value "{bit_width}" is not in {valid_widths}')
    validate_bool(little_e, 'little_e')

    # BUILD IT
    # Complex or Real
    if is_complex:
        data_format = data_format + 'c'
    else:
        data_format = data_format + 'r'
    # Data Type
    data_format = data_format + data_type.translate
    # Bit Width
    data_format = data_format + str(bit_width)
    # Endianness
    if bit_width > 8:
        if little_e:
            data_format = data_format + '_le'
        else:
            data_format = data_format + '_be'

    # DONE
    return data_format
