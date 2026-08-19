"""Defines common-use functionality on behalf of this package."""

# Standard Imports
from collections.abc import Callable
from pathlib import Path
# Third Party Imports
# Local Imports
from gallant_input.constants import SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT
from gallant_input.converters import convert_int_to_bin_bytes
from gallant_input.data_analysis import compare_streams
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.modem.calc import calculate_ber
from gallant_input.validation import (validate_binary_bytes, validate_bool, validate_callable,
                                      validate_file, validate_type)
from rxtx.argvals import ArgVals


def convert_data_len(data_len: int, max_bit_len: int = 8) -> bytes:
    """Convert the data length value into a binary value.

    Args:
        data_len: The integer to convert to binary.
        max_bit_len: Maximum length of the converted binary.
    """
    data_len_bits = convert_int_to_bin_bytes(number=data_len, min_width=max_bit_len)
    if len(data_len_bits) > max_bit_len:
        raise ValueError(f'The data_len value {data_len} does not fit into {max_bit_len} bits')
    return data_len_bits


def evaluate_payload(act_payload: bytes, exp_payload: bytes, debug: bool,
                     parse_payload: Callable[[bytes], None] | None = None) -> None:
    """Evaluate the actual payload against the expected payload with regard to the debug status.

    Args:
        act_payload: The observed payload to evaluate.
        exp_payload: The expected payload to compare the act_payload to.
        debug: Is debug mode enabled?  If True, increases the verbosity of the evaluation.
        parse_payload: [OPTIONAL] A callable to pass the act_payload to.
    """
    # INPUT VALIDATION
    validate_binary_bytes(act_payload, 'act_payload', exact_len=None)
    validate_binary_bytes(exp_payload, 'exp_payload', exact_len=None)
    validate_bool(debug, 'debug')
    if parse_payload is not None:
        validate_callable(parse_payload, 'parse_payload')

    # EVALUATE IT
    # Raw payload
    if debug:
        print(f'\nPAYLOAD: {act_payload}')
    # Parse payload
    if parse_payload is not None:
        parse_payload(act_payload)
    # Compare payloads
    if debug and exp_payload and exp_payload != act_payload:
        print(f'\nBER: {calculate_ber(exp_payload, act_payload)}')
        print('\nComparing the expected payload to the actual payload...')
        compare_streams(exp_payload, act_payload)


def get_filename(arg_vals: ArgVals) -> Path:
    """Form the filename argument into a Path object."""
    # LOCAL VARIABLES
    filename = None  # CLI argument filename as a Path obj

    # VALIDATION
    validate_type(arg_vals, 'arg_vals', ArgVals)

    # GET IT
    try:
        filename = Path(arg_vals.filename)
    except (ValueError, TypeError) as err:
        raise err from err

    # DONE
    return filename


def get_sample_rate(arg_vals: ArgVals, filepath: Path) -> float | int:
    """Get the sample rate, in order of priority, from: CLI args, filepath SigMF metadata."""
    # LOCAL VARIABLES
    sample_rate = None                                                # Sample rate
    meta_path = None                                                  # SigMF metadata filepath
    except_msg = 'Unable to fetch the sample rate from the CLI args'  # Base Exception message

    # VALIDATION
    validate_type(arg_vals, 'arg_vals', ArgVals)
    validate_file(filepath, 'filepath', must_exist=True)

    # GET IT
    # 1. CLI args?
    sample_rate = arg_vals.sample_rate
    # 2. SigMF?
    if sample_rate is None:
        # Fetch SigMF metadata (if available)
        if filepath.suffix.lower() == f'.{SIGMF_META_FILE_EXT}'.lower():
            meta_path = filepath
        elif filepath.suffix.lower() == f'.{SIGMF_DATA_FILE_EXT}'.lower():
            meta_path = filepath.with_suffix(f'.{SIGMF_META_FILE_EXT}')
        if meta_path:
            sig_meta_parser = SigMFMetaParser(meta_path)
            sample_rate = sig_meta_parser.get_sample_rate()

    # DONE
    if sample_rate is None:
        if meta_path is not None:
            except_msg = except_msg + f' or "{meta_path.absolute()}"'
        raise RuntimeError(except_msg)
    return sample_rate
