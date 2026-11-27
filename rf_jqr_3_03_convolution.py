"""This script utilizes GALLANT INPUT (GAIN) to demonstrate RF JQR 3.03 Convolution.

USAGE:
    python rf_jqr_3_03_convolution.py --num_taps 51 --freq_cutoff 0.25 --input_iq /tmp/input.iq \
    --threshold -20 --lowpass --output_iq /tmp/output.iq --coeff_output /tmp/taps.raw

EXAMPLE:
    # Linux
    cp ./data/qpsk_in_noise.sigmf-data /tmp/input.iq
    python rf_jqr_3_03_convolution.py --num_taps 51 --freq_cutoff 0.25 --input_iq /tmp/input.iq \
        --threshold -20 --lowpass --output_iq /tmp/output.iq --coeff_output /tmp/taps.raw

    # Windows
    copy .\\data\\qpsk_in_noise.sigmf-data C:\\Temp\\input1.sigmf-data
    copy .\\data\\qpsk_in_noise.sigmf-meta C:\\Temp\\input1.sigmf-meta
    python rf_jqr_3_03_convolution.py --num_taps 51 --freq_cutoff 0.25 `
        --input_iq C:\\Temp\\input1.sigmf-data --threshold -20 --lowpass `
        --output_iq C:\\Temp\\output1.iq --coeff_output C:\\Temp\\taps1.raw

    copy .\\data\\really-distinct-signal.sigmf-data C:\\Temp\\input2.sigmf-data
    copy .\\data\\really-distinct-signal.sigmf-meta C:\\Temp\\input2.sigmf-meta
    python rf_jqr_3_03_convolution.py --num_taps 51 --freq_cutoff 0.25 `
        --input_iq C:\\Temp\\input2.sigmf-data --threshold -17.5 `
        --output_iq C:\\Temp\\output2.iq --coeff_output C:\\Temp\\taps2.raw

"""

# Standard Imports
from pathlib import Path
from typing import Any, Final, Tuple
import argparse
# Third Party Imports
import numpy
# Local Imports
from gallant_input.constants import SIGMF_META_FILE_EXT
from gallant_input.filters import apply_fir, design_hpf, design_lpf
from gallant_input.io import read_samples, write_coeffs, write_samples
from gallant_input.plot import plot_frequency_response, plot_impulse_response, plot_spectrum
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.signal import convert_mag_to_db, compute_magnitude_spectrum, optimize_window_size
from gallant_input.validation import (validate_bool, validate_file, validate_int_or_float,
                                      validate_ndarray, validate_path, validate_string,
                                      validate_type)

CLI_ARG_FREQ_CUT: Final[str] = 'freq_cutoff'
CLI_ARG_INPUT_IQ: Final[str] = 'input_iq'
CLI_ARG_LOWPASS: Final[str] = 'lowpass'
CLI_ARG_NUM_TAPS: Final[str] = 'num_taps'
CLI_ARG_TAP_OUTPUT: Final[str] = 'coeff_output'
CLI_ARG_OUTPUT_IQ: Final[str] = 'output_iq'
CLI_ARG_THRESH: Final[str] = 'threshold'


def create_filter(lowpass: bool, numtaps: int, cutoff: float, out_file: Path) -> numpy.ndarray:
    """Design a filter, save the coefficients to out_file, and return the coefficients.

    Args:
        lowpass: If True, design a lowpass filter.  If False, filter will be a highpass.
        numtaps: Length of the filter.  Must be odd if not a lowpass filter.
        cutoff: Cutoff frequency of the filter as a ratio (0 < cutoff < 1).
        out_file: Output file to save the coefficients to.

    Returns:
        FIR filter coefficients in a numpy.ndarray object of length "numtaps".
    """
    # LOCAL VARIABLES
    filter_taps = None  # FIR filter coefficients in a numpy.ndarray object of length "numtaps

    # INPUT VALIDATION
    validate_bool(lowpass, 'lowpass')

    # CREATE IT
    if lowpass:
        filter_taps = design_lpf(numtaps=numtaps, cutoff=cutoff)
    else:
        filter_taps = design_hpf(numtaps=numtaps, cutoff=cutoff)

    # SAVE IT
    write_coeffs(coeffs=filter_taps, filename=out_file)

    # DONE
    return filter_taps


def parse_args() -> dict[str:Any]:
    """Parse the command line arguments.

    Returns:
        A dictionary of keys and their associataed values.
    """
    # LOCAL VARIABLES
    parser = None  # ArgumentParser object
    args = None    # Parsed argument Namespace

    # SETUP
    parser = argparse.ArgumentParser(prog='RF JQR 3.03',
                                     description='Demonstrate Convolution')
    # M: the number of taps in the filter
    parser.add_argument(f'-{CLI_ARG_NUM_TAPS[0]}', f'--{CLI_ARG_NUM_TAPS}', type=int,
                        action='store', help='The number of taps in the filter', required=True)
    # f_c: cutoff frequency as a fraction between 0 and 0.5 of the Nyquist frequency.
    parser.add_argument(f'-{CLI_ARG_FREQ_CUT[0]}', f'--{CLI_ARG_FREQ_CUT}', type=float,
                        action='store', help='Cutoff frequency as fraction between 0 and 0.5 '
                        'of the Nyquist frequency', required=True)
    # iq_filename: relative path to the input signal as a iq file containing complex samples.
    parser.add_argument(f'-{CLI_ARG_INPUT_IQ[0]}', f'--{CLI_ARG_INPUT_IQ}', type=str,
                        action='store', help='IQ file containing a signal as complex samples.',
                        required=True)
    # threshold: if the input signal's magnitude exceeds this threshold, the code will print all
    #   indices at which this occurs.
    parser.add_argument(f'-{CLI_ARG_THRESH[0]}', f'--{CLI_ARG_THRESH}', type=float, action='store',
                        help='Minimum magnitude, in decibels, to consider input signals.',
                        required=True)
    # lowpass: true if lowpass filter, false if highpass.
    parser.add_argument(f'--{CLI_ARG_LOWPASS}', action='store_true', default=False,
                        help='Create a lowpass filter (instead of a highpass filter).',
                        required=False)
    # test_filename: iq file containing the ideal filtered signal
    parser.add_argument(f'-{CLI_ARG_OUTPUT_IQ[0]}', f'--{CLI_ARG_OUTPUT_IQ}', type=str,
                        action='store', help='Output IQ file containing the filtered input signal.',
                        required=True)
    # tap_filename: name of the file where the filter coefficients will be written.
    parser.add_argument(f'-{CLI_ARG_TAP_OUTPUT[0]}', f'--{CLI_ARG_TAP_OUTPUT}', type=str,
                        action='store', help='Output file filter coefficients.', required=True)

    # PARSE IT
    args = parser.parse_args()

    # DONE
    return _construct_arg_dict(args=args)


def print_threshold_indices(samples: numpy.ndarray, threshold: int | float, use_db: bool = True,
                            title: str | None = 'Signal exceeds threshold at indices: ',
                            ) -> numpy.ndarray:
    """Print the indices of samples whose magnitude exceeds the threshold.

    Args:
        samples: A 1-dimensional array of samples to evaluate against the threhold.
        threshold: The minimum magnitude, linear or dB (as determined by use_db) for an index
            to qualify.
        use_db: [OPTIONAL] Convert the signal magnitude to decibels.
        title: [OPTIONAL] A preface before printing indices.  Will be ommitted if None.
    """
    # LOCAL VARIABLES
    mag_map = None  # Numpy.ndarray of magnitudes
    # INPUT VALIDATION
    validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                     must_be_complex=False)
    validate_int_or_float(validate_this=threshold, param_name='threshold')
    validate_bool(use_db, 'use_db')
    if title is not None:
        validate_string(title, 'title', can_be_empty=True)

    # SETUP
    mag_map = compute_magnitude_spectrum(samples)
    if use_db:
        mag_map = convert_mag_to_db(mag_map)

    # PRINT IT
    if title:
        print(title, end='')
    # My Way
    for index, mag in enumerate(mag_map):
        if mag > threshold:
            print(index, end=' ')
    print()


def main() -> None:
    """Demonstrate convolution.

    1. Read user input
    2. Write FIR coefficients to a file
    3. Display the impulse & frequency response of the filter
    4. Plot the before & after, in the frequency domain, of the filter applied to an input signal.
    5. Write the filtered signal to the output file
    6. Print the input signal's indices whose magnitude exceeds the threshold
    """
    # LOCAL VARIABLES
    arg_dict = parse_args()                           # 1. Read user input
    input_iq = Path(arg_dict[CLI_ARG_INPUT_IQ])       # Path object for the input IQ file
    output_iq = Path(arg_dict[CLI_ARG_OUTPUT_IQ])     # Path object for the output IQ file
    output_taps = Path(arg_dict[CLI_ARG_TAP_OUTPUT])  # Path object for the output taps file
    threshold = arg_dict[CLI_ARG_THRESH]              # The minimum threshold to print indices
    convert_db = True                                 # Convert magnitude to decibels
    imp_resp = None                                   # Impulse response designed from user input
    in_signal = None                                  # numpy.ndarray read from input_iq
    filt_signal = None                                # in_signal filtered with imp_resp
    samp_rate = None                                  # in_signal sample rate
    center_freq = None                                # in_signal center frequency

    # INPUT VALIDATION
    validate_file(input_iq, f'--{CLI_ARG_INPUT_IQ} value', must_exist=True)

    # DO IT
    # 2. Write FIR coefficients to a file
    imp_resp = create_filter(lowpass=arg_dict[CLI_ARG_LOWPASS], numtaps=arg_dict[CLI_ARG_NUM_TAPS],
                             cutoff=arg_dict[CLI_ARG_FREQ_CUT], out_file=output_taps)

    # 3. Display the impulse & frequency response of the filter
    # Plot impulse response
    plot_impulse_response(coeffs=imp_resp)
    # Plot frequency response
    plot_frequency_response(coeffs=imp_resp, win_size=optimize_window_size(coeffs=imp_resp))

    # 4. Plot the before & after, in the frequency domain, of the filter applied to an input signal.
    # Read the input signal
    in_signal = read_samples(input_iq)
    # Apply the FIR filter to the input signal
    filt_signal = apply_fir(samples=in_signal, coeffs=imp_resp)
    # Plot before, in the frequency domain
    # TO DO: DON'T DO NOW... Refactor center_freq args to also support integers
    samp_rate, center_freq = _gently_resolve_details(input_iq)
    plot_spectrum(samples=in_signal, samp_rate=samp_rate, convert_db=convert_db,
                  center_freq=center_freq, title=f'Magnitude Spectrum: {input_iq.name}')
    # Plot after, in the frequency domain
    plot_spectrum(samples=filt_signal, samp_rate=samp_rate, convert_db=convert_db,
                  center_freq=center_freq, title=f'Magnitude Spectrum: {output_iq.name}')

    # 5. Write the filtered signal to the output file
    write_samples(filename=output_iq, samples=filt_signal, overwrite=True)

    # 6. Print the input signal's indices whose magnitude exceeds the threshold
    print_threshold_indices(samples=in_signal, threshold=threshold, use_db=convert_db)


def _construct_arg_dict(args: argparse.Namespace) -> dict[str:Any]:
    """Construct an ArgVals data class from the parsed args."""
    # LOCAL VARIABLES
    arg_dict = {}  # Dictionary of args and their values
    arg_keys = [
        CLI_ARG_FREQ_CUT, CLI_ARG_INPUT_IQ, CLI_ARG_LOWPASS, CLI_ARG_NUM_TAPS,
        CLI_ARG_TAP_OUTPUT, CLI_ARG_OUTPUT_IQ, CLI_ARG_THRESH,
    ]

    # INPUT VALIDATION
    validate_type(var=args, var_name='args', var_type=argparse.Namespace)

    # GET IT
    for arg_key in arg_keys:
        arg_dict[arg_key] = _get_eafp_attr(args=args, attr=arg_key)

    # DONE
    return arg_dict


def _gently_resolve_details(filename: Path) -> Tuple[int, float]:
    """Gently attempt to divine the sample rate and center frequency of filename.

    Args:
        filename: A Path object that may or may not be a SigMF file format.

    Returns:
        If filename can be parsed as a SigMF dataset then this function will
        return tuple(samp_rate, center_freq).  Otherwise it returns tuple(None,None),
        which still happens to be valid input for those two arguments.

    Raises:
        TypeError: Bad data type.
    """
    # LOCAL VARIABLES
    samp_rate = None    # Sample rate divined from filename
    center_freq = None  # Center frequency divined from filename
    meta_path = None    # The SigMF metadata path, derived from filename
    meta_data = None    # The SigMFMetaParser() object to parse SigMF metadata

    # INPUT VALIDATION
    validate_path(filename, 'filename', must_exist=False)

    # RESOLVE IT
    try:
        meta_path = filename.with_suffix('.' + SIGMF_META_FILE_EXT)
        meta_data = SigMFMetaParser(meta_path)
        samp_rate = meta_data.get_sample_rate()
        center_freq = meta_data.get_center_freq() * 1.0
    except (FileNotFoundError, KeyError, RuntimeError, SyntaxError, TypeError, ValueError):
        pass  # We are ignoring all Exceptions in our pursuit of gently extracting information

    # DONE
    return tuple((samp_rate, center_freq))


def _get_eafp_attr(args: argparse.Namespace, attr: str) -> Any:
    """Safely retrieve values from a Namespace (if they exist)."""
    # LOCAL VARIABLES
    value = None  # Retrieved value

    # GET IT
    try:
        value = getattr(args, attr)
    except AttributeError:
        pass  # Easier to ask for forgiveness than permission (EAFP)

    # DONE
    return value


if __name__ == '__main__':
    main()
