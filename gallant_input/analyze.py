"""Defines functionality supporting the 'analyze' command."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.sigmfmetaparser import SigMFMetaParser
from gallant_input.validation import validate_type


def print_signal_parameters(meta_obj: SigMFMetaParser) -> None:
    """Print signal parameters from the provided SigMFMetaParser object.

    Args:
        meta_obj: SigMFMetaParser object constructed from the sigmf-meta file in question.

    Raises:
        FileNotFoundError: The underlying file is not found.
        KeyError: Invalid or missing key.
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES

    # INPUT VALIDATION
    validate_type(var=meta_obj, var_name='meta_obj', var_type=SigMFMetaParser)

    # PRINT IT
    # Center frequency
    print(f'Center Frequency: {meta_obj.get_center_freq()}hz')
    # Bandwidth
    # Frequency deviation
    # Burst length in symbols and seconds
    # Baud rate and bit rate
    # Preambles and Postambles
    # Repetitive segments
    # Consistent and variable data fields
