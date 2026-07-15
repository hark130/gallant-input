"""Intended as a menu of GAIN options for use in a static receiver.

1. Save the template with a unique module name and update the example usage in the module docstring.
2. Import the relevant Modem and ModemConfig child classes.
3. Update the build_modem() and build_modem_config() functions as appropriate.
4. Update the DEF_* and EXP_* macros.
5. Update parse_payload() as appropriate.
6. Run the module w/ --debug: fiddle with main() variables, disable unwanted plots, etc.

Example Usage:
    python -m rxtx.static_rx_template --help
"""

# Standard Imports
from pathlib import Path
from typing import Final
import sys
# Third Party Imports
import matplotlib.pyplot as plt
import numpy
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.constants import SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT
from gallant_input.converters import convert_bin_bytes_to_ascii
from gallant_input.data_analysis import compare_streams
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_ber, calculate_sps
from gallant_input.modem.modem import Modem
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.modscheme import ModScheme
from gallant_input.plot import (plot_spectrum, plot_symbol_boundaries, plot_time_domain,
                                plot_welch_psd)
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm
from gallant_input.validation import validate_file, validate_type
from rxtx.arg_parser import parse_args, print_help
from rxtx.argvals import ArgVals

DEF_PREAMBLE: Final[bytes] = b'01' * 32  # Example preamble (if necessary)
DEF_SYNCWORD: Final[bytes] = b'11010011100100011101001110010001'  # Example syncword (frame sync)
DEF_PREAMWRD: Final[bytes] = DEF_PREAMBLE[-8:] + DEF_SYNCWORD  # Some preamble + sw (if necessary?)
EXP_PAYLOAD: Final[bytes] = b'0100001101100001011011100010000001111001011011110111010100100000' \
                            b'0111001001100101011000010110010000100000011101000110100001101001' \
                            b'0111001100111111'  # Expected payload


# Remove this Pylint disable once these functions have been implemented
# pylint: disable=unused-argument
def build_modem(config: ModemConfig) -> Modem:
    """Build a Modem child class object."""
    modem_obj = None  # Modem child class object
    # modem_obj = OOK(config=config)  # Example
    return modem_obj
# pylint: enable=unused-argument


# Remove this Pylint disable once these functions have been implemented
# pylint: disable=unused-argument
def build_modem_config(sample_rate: float | int, symbol_rate: float | int, **kwargs) -> ModemConfig:
    """Build a ModemConfig child class object."""
    config = None  # ModemConfig child class object
    # config = OOKConfig(sample_rate=sample_rate, symbol_rate=symbol_rate, **kwargs)
    return config
# pylint: enable=unused-argument


def decide_symbols(symbol_metrics: numpy.ndarray, sample_rate: float | int,
                   symbol_rate: float | int) -> bytes:
    """Demodulate recovered symbols to binary bytes (Demod Step 3)."""
    # LOCAL VARIABLES
    config = build_modem_config(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Config obj
    modem = build_modem(config=config)                                             # Modem obj
    bin_bytes = b''                                                                # Binary output

    # DEMODULATE IT
    bin_bytes = modem.decide_symbols(symbol_metrics=symbol_metrics)

    # DONE
    return bin_bytes


def demod_to_metric(samples: numpy.ndarray, sample_rate: float | int,
                    symbol_rate: float | int) -> numpy.ndarray:
    """Demodulate a signal to a continuous-valued symbol metric (Demod Step 1)."""
    # LOCAL VARIABLES
    config = build_modem_config(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Config obj
    modem = build_modem(config=config)                                             # Modem obj
    symbol_metrics = None                                                          # Symbol metrics

    # DEMODULATE IT
    symbol_metrics = modem.demodulate_to_metric(samples=samples)

    # DONE
    return symbol_metrics


def demodulate(samples: numpy.ndarray, sample_rate: float | int,
               symbol_rate: float | int) -> bytes:
    """Completeely demodulate a signal to binary bytes (Demod Steps 1 - 3)."""
    # LOCAL VARIABLES
    config = build_modem_config(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Config obj
    modem = build_modem(config=config)                                             # Modem obj
    bin_bytes = b''                                                                # Binary output

    # DEMODULATE IT
    bin_bytes = modem.demodulate(samples=samples)  # Full demod

    # DONE
    return bin_bytes


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


def parse_payload(payload: bytes) -> None:
    """Parse and print the payload."""
    # PARSE IT
    message = convert_bin_bytes_to_ascii(payload)  # Example

    # PRINT IT
    print(f'\nMESSAGE: {message}')


# Don't you know it's CFT, Pylint?!
# pylint: disable=broad-exception-caught,too-many-branches,too-many-locals,too-many-statements
def main() -> None:
    """do_it()."""
    arg_vals = None  # Parsed CLI args
    try:
        # LOCAL VARIABLES
        arg_vals = parse_args()             # Parsed CLI args
        filepath = get_filename(arg_vals)   # CLI capture file
        sample_rate = 0                     # Capture sample rate
        symbol_rate = arg_vals.symbol_rate  # Capture symbol rate
        sps = 0                             # Samples per symbol
        samples = None                      # Samples read from the capture
        decimate = 20                       # Decimation
        squelch_db = None                   # Squelch threshold in db (e.g., -48, -55) or None
        spect_analysis = None               # SpectrumAnalysis obj
        det_signal = None                   # DetectedSignal obj
        metric = None                       # Step 1 - Continuous symbol metric at orig. sample rate
        symbol_metrics = None               # Step 2 - Recovered symbol metric for each orig. symbol
        binary = b''                        # Step 3 - Demodulated binary
        needle = b''                        # The needle being correlated to the package (e.g., sw)
        index = 0                           # Correlated index into the binary
        payload = b''                       # Frame synch'd binary

        # PREPARE
        # [!] Determine sample rate
        sample_rate = get_sample_rate(arg_vals, filepath)
        # [!] Get Samples
        samples = read_samples(filepath)
        # [!] Establish samples-per-symbol
        sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)
        if arg_vals.debug:
            plot_time_domain(samples=samples, samp_rate=sample_rate,
                             title='Time Domain (original)', now=False)
            plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
                          convert_db=True, center_freq=None,
                          title='Magnitude Spectrum (original)', now=False)

        # [?] Clean Up
        # Decimate!
        if decimate > 1:
            samples = decimate_samples(samples=samples, decimate=decimate)
            sample_rate = sample_rate / decimate  # Update the sample rate
            sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Calc new sps
        if arg_vals.debug:
            plot_time_domain(samples=samples, samp_rate=sample_rate,
                             title='Time Domain (post-decimation)', now=False)
            plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
                          convert_db=True, center_freq=None,
                          title='Magnitude Spectrum (post-decimation)', now=False)

        # [?] Squelch!
        # Identify noise floor
        if arg_vals.debug:
            plot_welch_psd(samples=samples, sample_rate=sample_rate,
                           title='Welch Power Spectral Density (pre-squelch)', now=False)
        # Squelch?
        if squelch_db is not None:
            samples = squelch_signal(samples=samples, threshold=squelch_db)
            # Squelch Results
            if arg_vals.debug:
                plot_welch_psd(samples=samples, sample_rate=sample_rate,
                               title='Welch Power Spectral Density (post-squelch)', now=False)

        # [?] Analyze the Spectrum
        spect_analysis = analyze_spectrum(samples, sample_rate=sample_rate, max_peaks=2)

        # [?] Detect Signal
        det_signal = detect_signal(analysis=spect_analysis, scheme=ModScheme.FSK2)

        # [?] Downconvert
        if det_signal.center_frequency > 0 or det_signal.center_frequency < 0:
            samples = downconvert_signal(samples=samples, sample_rate=sample_rate,
                                         center_freq=det_signal.center_frequency)
            if arg_vals.debug:
                plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
                              convert_db=True, center_freq=None,
                              title='Magnitude Spectrum (post-baseband translation)', now=False)

        # DEMOD
        # [?] Steps 1 - 3?
        binary = demodulate(samples=samples, sample_rate=sample_rate, symbol_rate=symbol_rate)
        # -or-
        # [?] Step 1, 2, then 3!
        if not binary:
            # Step 1 - Demod to Metrics
            metric = demod_to_metric(samples=samples, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate)  # Reshaped to symbol boundaries
            if arg_vals.debug:
                plot_time_domain(samples=metric, samp_rate=sample_rate,
                                 title='Time Domain (Demod Step 1: Metrics)', now=False)
                plot_symbol_boundaries(real_wave=metric, sps=sps,
                                       title='Symbol Boundaries (Demod Step 1: Metrics)', now=False)
            # Step 2 - Time Sync w/ Interpolation(?)
            # symbol_metrics = recover_clock_mm(metric, sps, interp=None)  # Do not interpolate
            symbol_metrics = recover_clock_mm(metric, sps, interp=16)  # Interp for better boundary
            if arg_vals.debug:
                plot_time_domain(samples=symbol_metrics, samp_rate=sample_rate,
                                 title='Time Domain (Demod Step 2: Symbol Metrics)', now=False)
                plot_symbol_boundaries(real_wave=symbol_metrics, sps=1,
                                       title='Symbol Boundaries (Demod Step 2: Symbol Metrics)',
                                       now=False)
            # Step 3 - Symbol Decisions
            binary = decide_symbols(symbol_metrics=symbol_metrics, sample_rate=sample_rate,
                                    symbol_rate=symbol_rate)
        if arg_vals.debug:
            print(f'Demod Final Step: {binary}')

        # [?] Frame Sync
        needle = DEF_SYNCWORD
        index = correlate_it(binary, needle)
        payload = binary[index + len(needle):]

        # [!] Parse Payload
        if arg_vals.debug:
            print(f'\nPAYLOAD: {payload}')
        parse_payload(payload)
        if arg_vals.debug and EXP_PAYLOAD and EXP_PAYLOAD != payload:
            print(f'\nBER: {calculate_ber(EXP_PAYLOAD, payload)}')
            print('\nComparing the expected payload to the actual payload...')
            compare_streams(EXP_PAYLOAD, payload)
    except Exception as err:
        print(f'Execution failed with: {repr(err)}', file=sys.stderr, flush=True)
        print_help()
        if arg_vals is None or arg_vals.debug is True:
            raise err from err
    finally:
        if arg_vals is not None and arg_vals.debug is True:
            plt.show()  # Plot them all *now*
# pylint: enable=broad-exception-caught,too-many-branches,too-many-locals,too-many-statements


if __name__ == '__main__':
    main()
