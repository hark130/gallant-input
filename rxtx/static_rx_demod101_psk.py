"""Intended as a menu of GAIN options for use in a static receiver.

Written specifically for use with Demod 101's BPSK filtered signal, downconverted to baseband.

Example Usage:
    python -m rxtx.static_rx_demod101_psk --help
    python -m rxtx.static_rx_demod101_psk --baud 1200 `
        --filename ./test/test_input/bpsk_mod1_c0hz_s4800_b1200.sigmf-data
"""

# Standard Imports
from pathlib import Path
from typing import Final
import sys
# Third Party Imports
import matplotlib.pyplot as plt
import numpy
# Local Imports
# from gallant_input.analyze import analyze_spectrum
from gallant_input.constants import SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT
from gallant_input.converters import convert_bin_bytes_to_ascii
from gallant_input.data_analysis import compare_streams
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_ber, calculate_sps
from gallant_input.modem.modem import Modem
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.modem.bpsk import BPSK
from gallant_input.modem.bpsk_config import BPSKConfig
from gallant_input.modem.matched_filter import MatchedFilter
from gallant_input.modscheme import ModScheme
from gallant_input.plot import plot_spectrum, plot_symbol_boundaries, plot_time_domain
# from gallant_input.plot import plot_welch_psd
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.synch.costas_loop import CostasLoop
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm
from gallant_input.validation import validate_file, validate_type
from rxtx.arg_parser import parse_args, print_help
from rxtx.argvals import ArgVals

DEF_PREAMBLE: Final[bytes] = b'01' * 16  # Actual preamble
DEF_SYNCWORD: Final[bytes] = b'1101001110010001'  # Syncword
DEF_PREAMWRD: Final[bytes] = DEF_PREAMBLE[-8:] + DEF_SYNCWORD  # Some preamble + sw
EXP_PAYLOAD: Final[bytes] = b'0100110001101111011011110110101101110011001000000110110001101001' \
                            b'0110101101100101001000000111100101101111011101010010000001100111' \
                            b'0110111101110100001000000110100101110100001000010010000001010100' \
                            b'0110100001101001011100110010000001101001011100110010000001000100' \
                            b'0110010101101101011011110110010000100000001100010011000000110001' \
                            b'0010000001110000011000010111001001110100001000000011001100101110' \
                            b'0010000001100110011011000110000101100111011110110110100101110100' \
                            b'0111001101011111011010100111010100110101011101000101111101100001' \
                            b'01011111011100000110100000110100010100110110010101111101'  # Payload


def build_modem(config: ModemConfig) -> Modem:
    """Build a Modem child class object."""
    modem_obj = BPSK(config=config)  # Modem child class object
    return modem_obj


def build_modem_config(sample_rate: float | int, symbol_rate: float | int,
                       carrier_recovery: CostasLoop | None, **kwargs) -> ModemConfig:
    """Build a ModemConfig child class object."""
    # ModemConfig child class object
    config = BPSKConfig(sample_rate=sample_rate, symbol_rate=symbol_rate,
                        carrier_recovery=carrier_recovery, **kwargs)
    return config


def decide_symbols(symbol_metrics: numpy.ndarray, sample_rate: float | int,
                   symbol_rate: float | int, carrier_recovery: CostasLoop | None) -> bytes:
    """Demodulate recovered symbols to binary bytes (Demod Step 3)."""
    # LOCAL VARIABLES
    config = build_modem_config(sample_rate, symbol_rate, carrier_recovery)  # Config obj
    modem = build_modem(config=config)                                       # Modem obj
    bin_bytes = b''                                                          # Binary output

    # DEMODULATE IT
    bin_bytes = modem.decide_symbols(symbol_metrics=symbol_metrics)

    # DONE
    return bin_bytes


def demod_to_metric(samples: numpy.ndarray, sample_rate: float | int,
                    symbol_rate: float | int, carrier_recovery: CostasLoop | None) -> numpy.ndarray:
    """Demodulate a signal to a continuous-valued symbol metric (Demod Step 1)."""
    # LOCAL VARIABLES
    config = build_modem_config(sample_rate, symbol_rate, carrier_recovery)  # Config obj
    modem = build_modem(config=config)                                       # Modem obj
    symbol_metrics = None                                                    # Symbol metrics

    # DEMODULATE IT
    symbol_metrics = modem.demodulate_to_metric(samples=samples, filt=MatchedFilter.NONE)

    # DONE
    return symbol_metrics


def demodulate(samples: numpy.ndarray, sample_rate: float | int,
               symbol_rate: float | int, carrier_recovery: CostasLoop | None) -> bytes:
    """Completeely demodulate a signal to binary bytes (Demod Steps 1 - 3)."""
    # LOCAL VARIABLES
    config = build_modem_config(sample_rate, symbol_rate, carrier_recovery)  # Config obj
    modem = build_modem(config=config)                                       # Modem obj
    bin_bytes = b''                                                          # Binary output

    # DEMODULATE IT
    bin_bytes = modem.demodulate(samples=samples)  # Full demod

    # DONE
    return bin_bytes


def evaluate_payload(act_payload: bytes, exp_payload: bytes, debug: bool) -> None:
    """Evaluate the actual payload against the expected payload with regard to the debug status."""
    if debug:
        print(f'\nPAYLOAD: {act_payload}')
    parse_payload(act_payload)
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


def parse_payload(payload: bytes) -> None:
    """Parse and print the payload."""
    # PARSE IT
    message = convert_bin_bytes_to_ascii(payload[:payload.find(b'00000000')])  # Stop at nul char

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
        carrier_recovery = None             # Optional carrier recovery
        sps = 0                             # Samples per symbol
        samples = None                      # Samples read from the capture
        decimate = 2                        # Decimation (e.g., 1 to skip decimation)
        squelch_db = None                   # Squelch threshold in db (e.g., -48, -55); skip w/ None
        mod_scheme = ModScheme.BPSK         # Communicates anticipated modulation to detect_signal()
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
        #     plot_time_domain(samples=samples, samp_rate=sample_rate,
        #                      title='Time Domain (original)', now=False)
        #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
        #                   convert_db=True, center_freq=None,
        #                   title='Magnitude Spectrum (original)', now=False)

        # [?] Clean Up
        # Decimate!
        if decimate > 1:
            samples = decimate_samples(samples=samples, decimate=decimate)
            sample_rate = sample_rate / decimate  # Update the sample rate
            sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Calc new sps
        if sps > 20 and arg_vals.debug:
            print(f'Consider decimating the samples-per-symbol, currently "{sps}", below 20')
        # if arg_vals.debug:
        #     plot_time_domain(samples=samples, samp_rate=sample_rate,
        #                      title='Time Domain (post-decimation)', now=False)
        #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
        #                   convert_db=True, center_freq=None,
        #                   title='Magnitude Spectrum (post-decimation)', now=False)

        # [?] Squelch!
        # Identify noise floor
        # if arg_vals.debug:
        #     plot_welch_psd(samples=samples, sample_rate=sample_rate,
        #                    title='Welch Power Spectral Density (pre-squelch)', now=False)
        # Squelch?
        if squelch_db is not None:
            samples = squelch_signal(samples=samples, threshold=squelch_db)
            # Squelch Results
            # if arg_vals.debug:
            #     plot_welch_psd(samples=samples, sample_rate=sample_rate,
            #                    title='Welch Power Spectral Density (post-squelch)', now=False)

        # [?] Analyze the Spectrum
        # Signal is already at baseband, so no need to analyze, detect, and downconvert
        # spect_analysis = analyze_spectrum(samples, sample_rate=sample_rate, max_peaks=2)

        # [?] Detect Signal
        if spect_analysis is not None:
            try:
                det_signal = detect_signal(analysis=spect_analysis, scheme=mod_scheme)
            except NotImplementedError as err:
                if arg_vals.debug:
                    print(f'No support for this modulation scheme yet (see: GAIN-24): {err}')
            else:
                if arg_vals.debug:
                    print('Any support for this modulation scheme is likely wrong (see: GAIN-24)')

        # [?] Downconvert
        if det_signal is not None:
            if det_signal.center_frequency > 0 or det_signal.center_frequency < 0:
                samples = downconvert_signal(samples=samples, sample_rate=sample_rate,
                                             center_freq=det_signal.center_frequency)
                if arg_vals.debug:
                    plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
                                  convert_db=True, center_freq=None,
                                  title='Magnitude Spectrum (post-baseband translation)', now=False)

        # DEMOD
        # NOTE: Modem() and ModemConfig() objects are (essentially) reset between these
        # non-demodulate() helper function calls.  If your Modem*() objects need to maintain
        # state (e.g., recovering carrier phase over chunked samples) then consider skipping the
        # helper functions and calling direct to the source.
        # [?] Step 0 - Recover Carrier?!
        # loop_band = 0.0628  # GNU Radio value
        # loop_band = 0.05  # WORKS WITH...
        loop_band = 0.035  # ...OR THIS (barely) AND...
        # loop_band = 0.03  # but not this (BER: 0.0017605633802816902; "Loks like...")
        # damp_fact = 0.707  # Default value
        damp_fact = 0.707  # ...THIS!
        # Recover carrier phase
        carrier_recovery = CostasLoop(loop_bandwidth=loop_band, damping_factor=damp_fact)
        # [?] Steps 1 - 3?
        # binary = demodulate(samples=samples, sample_rate=sample_rate, symbol_rate=symbol_rate,
        #                     carrier_recovery=carrier_recovery)
        # -or-
        # [?] Step 1, 2, then 3!
        if not binary:
            # Step 1 - Demod to Metrics
            metric = demod_to_metric(samples=samples, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate, carrier_recovery=carrier_recovery)
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
                                    symbol_rate=symbol_rate, carrier_recovery=carrier_recovery)
        if arg_vals.debug:
            print(f'Demod Final Step: {binary}')

        # [?] Frame Sync
        needle = DEF_SYNCWORD
        index = correlate_it(binary, needle)
        payload = binary[index + len(needle):]

        # [!] Parse Payload
        evaluate_payload(act_payload=payload, exp_payload=EXP_PAYLOAD, debug=arg_vals.debug)
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
