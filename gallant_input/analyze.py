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
    low_freq = None   # Frequency lower edge as a float
    high_freq = None  # Frequency upper edge as a float

    # INPUT VALIDATION
    validate_type(var=meta_obj, var_name='meta_obj', var_type=SigMFMetaParser)

    # PRINT IT
    # Center frequency
    print(f'Center Frequency: {meta_obj.get_center_freq()} Hz')
    # Bandwidth
    print(f'Bandwidth: {meta_obj.get_bandwidth()} Hz')
    # Frequency deviation
    (low_freq, high_freq) = meta_obj.determine_freq_range()
    print(f'Frequency Deviation\n\tLow:  {low_freq} Hz\n\tHigh: {high_freq} Hz')
    # Burst length in symbols and seconds
    # Baud rate and bit rate
    # Preambles and Postambles
    # Repetitive segments
    # Consistent and variable data fields
