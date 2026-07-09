"""Intended as a menu of GAIN options for use in a static receiver.

Example Usage:
    python -m rxtx.static_rx_demod101_fsk --help
    python -m rxtx.static_rx_demod101_fsk --filename ./test/test_input/bfsk_c434p1_s240k_b600.sigmf-data --baud 600
    python -m rxtx.static_rx_demod101_fsk --filename ./test/test_input/bfsk_mod4_c0hz_s240k_b600.sigmf-data --baud 600
"""

# Standard Imports
from pathlib import Path
from typing import Final
import sys
# Third Party Imports
import numpy
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.constants import SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT
from gallant_input.converters import convert_bin_bytes_to_ascii
from gallant_input.data_analysis import compare_streams
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_ber, calculate_sps
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modem.modem import Modem
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.modscheme import ModScheme
from gallant_input.plot import plot_spectrum, plot_time_domain
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm
from gallant_input.validation import validate_file, validate_type
from rxtx.arg_parser import parse_args, print_help
from rxtx.argvals import ArgVals

DEF_PREAMBLE: Final[bytes] = b'01' * 32  # Preamble
DEF_SYNCWORD: Final[bytes] = b'1101001110010001'  # Syncword
DEF_PREAMWRD: Final[bytes] = DEF_PREAMBLE[-8:] + DEF_SYNCWORD  # Some preamble + sw (if necessary?)
EXP_PAYLOAD: Final[bytes] = b'0101011101100101011011000110001101101111011011010110010100100000' \
                            b'0110001001100001011000110110101100100001001000000101010001101000' \
                            b'0110100101110011001000000110100101110011001000000100010001100101' \
                            b'0110110101101111011001000010000000110001001100000011000100100000' \
                            b'0111000001100001011100100111010000100000001100100010111000100000' \
                            b'0110011001101100011000010110011101111011011001100111001000110011' \
                            b'0111000101110101010001010110111001000011011110010101111101110011' \
                            b'0100100000110001010001100011011101011111011010110011001101111001' \
                            b'00110001011011100100011101111101'  # Expected payload


def build_modem(config: ModemConfig) -> FSK2:
    """Build a Modem child class object."""
    modem_obj = FSK2(config=config)  # Modem child class object
    return modem_obj


def build_modem_config(sample_rate: float | int, symbol_rate: float | int, **kwargs) -> FSK2Config:
    """Build a ModemConfig child class object."""
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate,
                        freq0=0, freq1=0, **kwargs)  # ModemConfig child class object
    return config


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

# TESTING POC CODE
# TODO: Clean this up later
from noise_poc import plot_sample_mag, plot_sample_mag_db, plot_welch_psd, estimate_noise_floor


# pylint: disable=broad-exception-caught,too-many-locals
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
        decimate = 1                        # Decimation
        # LOCAL NOTE:
        # For mod4 (see: module docstring)
        #   Squelch of -7 yielded a BER of 0.02389705882352941
        #   No squelch (see: None) yielded a BER of 0.03125
        #   Just about all other values yielded a BER of exactly 0.04595588235294118
        # For c434p1 (see: module docstring)
        #   Squelch of -7 yielded a BER of 0.01838235294117647!!!
        squelch_db = -7                     # Squelch threshold in db (e.g., -48, -55) or None
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
        # if arg_vals.debug:
        #     plot_time_domain(samples=samples, samp_rate=sample_rate)
        #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
        #                   convert_db=True, center_freq=None)

        # POC TESTING... TODO: Clean this up later
        print(f'ESTIMATED NOISE FLOOR: {estimate_noise_floor(samples, sample_rate)}')
        # plot_sample_mag(samples)
        # plot_sample_mag_db(samples)
        plot_welch_psd(samples, sample_rate)

        # [?] Clean Up
        # Decimate!
        if decimate > 1:
            samples = decimate_samples(samples=samples, decimate=decimate)
            sample_rate = sample_rate / decimate  # Update the sample rate
            sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Calc new sps
        # if arg_vals.debug:
        #     plot_time_domain(samples=samples, samp_rate=sample_rate,
        #                      title='Time Domain (post-decimation)')
        #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
        #                   convert_db=True, center_freq=None,
        #                   title='Magnitude Spectrum (post-decimation)')

        # [?] Squelch!
        # Identify noise floor
        if arg_vals.debug:
            plot_welch_psd(samples, sample_rate)
        if squelch_db is not None:
            samples = squelch_signal(samples=samples, threshold=squelch_db)
        # if arg_vals.debug:
        #     plot_time_domain(samples=samples, samp_rate=sample_rate,
        #                      title='Time Domain (post-decimated squelch)')
        #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
        #                   convert_db=True, center_freq=None,
        #                   title='Magnitude Spectrum (post-decimated squelch)')
        print(f'ESTIMATED NOISE FLOOR (post-squelch): {estimate_noise_floor(samples, sample_rate)}')
        # plot_welch_psd(samples, sample_rate)

        # [?] Analyze the Spectrum
        spect_analysis = analyze_spectrum(samples, sample_rate=sample_rate, max_peaks=2)

        # [?] Detect Signal
        det_signal = detect_signal(analysis=spect_analysis, scheme=ModScheme.FSK2)

        # [?] Downconvert
        if det_signal.center_frequency > 0 or det_signal.center_frequency < 0:
            samples = downconvert_signal(samples=samples, sample_rate=sample_rate,
                                         center_freq=det_signal.center_frequency)
            # if arg_vals.debug:
            #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
            #                   convert_db=True, center_freq=None,
            #                   title='Magnitude Spectrum (post-baseband translation)')

        # DEMOD
        # [?] Steps 1 - 3?
        # binary = demodulate(samples=samples, sample_rate=sample_rate, symbol_rate=symbol_rate)
        # -or-
        # [?] Step 1, 2, then 3!
        if not binary:
            # Step 1 - Demod to Metrics
            metric = demod_to_metric(samples=samples, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate)  # Reshaped to symbol boundaries
            # if arg_vals.debug:
            #     plot_time_domain(samples=metric, samp_rate=sample_rate,
            #                      title='Time Domain (Demod Step 1: Metrics)')
            # Step 2 - Time Sync w/ Interpolation
            # symbol_metrics = recover_clock_mm(metric, sps, interp=None)  # Do not interpolate
            symbol_metrics = recover_clock_mm(metric, sps, interp=16)  # Interp for better boundary
            if arg_vals.debug:
                plot_time_domain(samples=symbol_metrics, samp_rate=sample_rate,
                                 title='Time Domain (Demod Step 2: Symbol Metrics)')
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
        if arg_vals.debug and EXP_PAYLOAD != payload:
            print(f'\nBER: {calculate_ber(EXP_PAYLOAD, payload)}')
            print('\nComparing the expected payload to the actual payload...')
            compare_streams(EXP_PAYLOAD, payload)
    except Exception as err:
        print(f'Execution failed with: {repr(err)}', file=sys.stderr, flush=True)
        print_help()
        if arg_vals is None:
            raise err from err
        elif arg_vals.debug is True:
            raise err from err
# pylint: enable=broad-exception-caught,too-many-locals


if __name__ == '__main__':
    main()
