"""Intended as a menu of GAIN options for use in a static receiver.

4. Update the DEF_* and EXP_* macros.
5. Update parse_payload() as appropriate.
7. Run the module w/ --debug:
    - fiddle with main() variables (e.g., decimate, squelch_db)
    - disable unwanted plots
    - etc.

Specific Usage:
    python -m rxtx.static_rx_rds_psk --help
    python -m rxtx.static_rx_rds_psk --baud 1187.5 `
        --filename ./test/test_input/bpsk_mod2_c0hz_s19k_b1187p5.sigmf-data
"""

# Standard Imports
from typing import Final
import sys
# Third Party Imports
import matplotlib.pyplot as plt
import numpy
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.codec import decode_differential_binary
from gallant_input.converters import convert_bin_bytes_to_ascii, sanitize_ascii
from gallant_input.data_analysis import find_common_repeats
from gallant_input.io import read_samples
from gallant_input.modem.bpsk import BPSK
from gallant_input.modem.bpsk_config import BPSKConfig
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.matched_filter import MatchedFilter
from gallant_input.modem.modem import Modem
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.modscheme import ModScheme
from gallant_input.plot import (plot_spectrum, plot_symbol_boundaries, plot_time_domain,
                                plot_welch_psd)
from gallant_input.rds.block import RDSBlock
from gallant_input.rds.block_id import BlockID
from gallant_input.rds.collection import RDSCollection
from gallant_input.rds.constants import RDS_BLOCK_LEN, RDS_GROUP_LEN
from gallant_input.rds.exceptions import RDSBlockIDMismatch, RDSIntegrityFailure
from gallant_input.rds.group import RDSGroup
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.synch.costas_loop import CostasLoop
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm
from rxtx.arg_parser import parse_args, print_help
from rxtx.utilities import evaluate_payload, get_filename, get_sample_rate

DEF_PREAMBLE: Final[bytes] = b'01' * 32  # Example preamble (if necessary)
DEF_SYNCWORD: Final[bytes] = b'11010011100100011101001110010001'  # Example syncword (frame sync)
DEF_PREAMWRD: Final[bytes] = DEF_PREAMBLE[-8:] + DEF_SYNCWORD  # Some preamble + sw (if necessary?)
EXP_PAYLOAD: Final[bytes] = b"0000000000000010001000000101010111000001010101000100000000001001" \
                            b"1001010010000111001101110011011001110011011001010110000100000110" \
                            b"0101010100000111010101011100000000010010101011111100101100110111" \
                            b"0011011010110011011011000010111001001111100101011111101110101001" \
                            b"1110000100001001000101101011110011011000110100100010000110110011" \
                            b"0011101000000100110010101110001110101010111000000000100101011100" \
                            b"1001011110011011100110110101100110010000000100000001101110001010" \
                            b"1110001110101010111000000000100101000001000000011001101110011011" \
                            b"0101100110010000001010010101110000101010111000111010101011100000" \
                            b"0000100101001010011100111001101110011011010110011011001010110000" \
                            b"1000001100101010111000111010101011100001000010010001110111001110" \
                            b"1101001011011101001111001011001110010111011000000110101011100011" \
                            b"1010101011100000000010010100000100000001100110111001101101011001" \
                            b"1001000000101011100000001010101011100011101010101110000000001001" \
                            b"0100101001110011100110111001101101011001101100001011110011111010" \
                            b"1010101011100011101010101110000000001001010101111110010110011011" \
                            b"1001101101011001101000110010011010001001011010101110001110101010" \
                            b"1110000100001001001001101110001001000000101010111101010110111000" \
                            b"0011000101001110101010101110001110101010111000000000100101011100" \
                            b"1001011110011011100110110101100110010000000100000001101110001010" \
                            b"1110001110101010111000000000100101000001000000011001101110011011" \
                            b"0101100110010000001010111000000010101010111000111010101011100000" \
                            b"0000100101001010011100111001101110011011010110011011000010111100" \
                            b"1111101010101010111000111010101011100001000010010010110110010000" \
                            b"1100101011000010011000101011101000010111001011011000101011100011" \
                            b"1010101011100000000010010101011111100101100110111001101101011001" \
                            b"1010001100100110100010010110101011100011101010101110000000001001" \
                            b"0101110010010111100110111001101101011001100100000001000000011011" \
                            b"1000101011100011101010101110000000001001010000010000000110011011" \
                            b"1001101101011001100100000010101110000000101010101110001110101010" \
                            b"1110000100001001001100000000011001000000101001010001111010110010" \
                            b"1011000010000011001010101110001110101010111000000000100101001010" \
                            b"0111001110011011100110110101100110110000101111001111101010101010" \
                            b"1110001110101010111000000000100101010111111001011001101110011011" \
                            b"0101100110100011001001101000100101101010111000111010101011100000" \
                            b"0000100101011100100101111001101110011011010110011001000000010000" \
                            b"0001101110001010111000111010101011100001000010010011101101110100" \
                            b"1101100001011100111100010001000000000110111111111000101011100011" \
                            b"1010101011100000000010010100000100000001100110111001101101011001" \
                            b"1001000000101011100000001010101011100011101010101110000000001001" \
                            b"0100101001110011100110111001101101011001101100001011110011111010" \
                            b"1010101011100011101010101110000000001001010101111110010110011011" \
                            b"1001101101011001101000110010011010001001011010101110001110101010" \
                            b"1110000100001001000000000101100010101110110000101110110010111100" \
                            b"1010001100001101010010101110001110101010111000000000100101011100" \
                            b"1001011110011011100110110101100110010000000100000001101110001010" \
                            b"1110001110101010111000000000100101000001000000011001101110011011" \
                            b"0101100110101010101110000101011101101010111000111010101011100000" \
                            b"0000100101001010011100111001101110011011010110011011011000110100" \
                            b"1001001111101010111000111010101011100001000010010000101100101010" \
                            b"1001101001000000110111101010101010111000010101110110101011100011" \
                            b"1010101011100000000010010101011111100101100110111001101101011001" \
                            b"1011001100111010000001001100101011100011101010101110000000001001" \
                            b"0101110010010111100110111001101101011001101101001011011101010100" \
                            b"1010101011100011101010101110000000001001010000010000000110011011" \
                            b"1001101101011001101010101011100001010111011010101110001110101010" \
                            b"1110000100001001000101101011110011011000110100100010000110110011" \
                            b"0011101000000100110010101110001110101010111000000000100101001010" \
                            b"0111001110011011100110110101100110110110001101001001001111101010" \
                            b"1110001110101010111000000000100101010111111001011001101110011011" \
                            b"0101100110110011001110100000010011001010111000111010101011100000" \
                            b"0000100101011100100101111001101110011011010110011011010010110111" \
                            b"0101010010101010111000111010101011100001000010010001110111001110" \
                            b"1101001011011101001111001011001110010111011000000110101011100011" \
                            b"1010101011100000000010010100000100000001100110111001101101011001" \
                            b"1010101010111000010101110110101011100011101010101110000000001001" \
                            b"0100101001110011100110111001101101011001101101100011010010010011" \
                            b"1110101011100011101010101110000000001001010101111110010110011011" \
                            b"1001101101011001101100110011101000000100110010101110001110101010" \
                            b"1110000100001001001001101110001001000000101010111101010110111000" \
                            b"0011000101001110101010101110001110101010111000000000100101011100" \
                            b"1001011110011011100110110101100110110100101101110101010010101010" \
                            b"1110001110101010111000000000100101000001000000011001101110011011" \
                            b"0101100110101010101110000101011101101010111000111010101011100000" \
                            b"0000100101"  # Expected payload


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


def calculate_success_rate(exp_num: int, act_num: int) -> float:
    """Calculate a percentage success rate from the expected number and the actual number."""
    return round(act_num / exp_num, 5) * 100


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
                    symbol_rate: float | int, carrier_recovery: CostasLoop | None,
                    filt: MatchedFilter) -> numpy.ndarray:
    """Demodulate a signal to a continuous-valued symbol metric (Demod Step 1)."""
    # LOCAL VARIABLES
    config = build_modem_config(sample_rate, symbol_rate, carrier_recovery)  # Config obj
    modem = build_modem(config=config)                                       # Modem obj
    symbol_metrics = None                                                    # Symbol metrics

    # DEMODULATE IT
    symbol_metrics = modem.demodulate_to_metric(samples=samples, filt=filt)

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


def parse_rds_traffic(payload: bytes, exp_num_picodes: int,
                      exp_num_groups: int, debug: bool) -> None:
    """Parse and print the RDS traffic from the payload."""
    # PARSE IT
    message = payload             # Parse the payload into a collection of RDS Groups
    collection = RDSCollection()  # Collection of valid RDS Groups
    act_num_groups = 0            # Actual number of RDS Groups parsed

    # PARSE IT
    first_index = None
    last_index = 0
    for index, _ in enumerate(payload):
        # Is this an RDSBlock?  Guess.
        tmp_block = RDSBlock(payload[index:index+RDS_BLOCK_LEN], BlockID.GUESS)
        try:
            tmp_block.verify_block_integrity(force=True)  # Valid?
            tmp_block_data = tmp_block.get_block_data()
        except RDSIntegrityFailure:
            continue  # It's not an RDS Block.  Quietly keep looking...
        except ValueError:
            break  # Ran out of bits
        # else:
        #     print(f'Index "{index}" contains an RDS Block of ID "{tmp_block.get_block_id().name}" '
        #           f'with data: {tmp_block_data} '
        #           f'({convert_bin_bytes_to_ascii(tmp_block_data, clean_it=True)})')
        # Is this an RDSGroup?
        tmp_group = RDSGroup(payload[index:index+RDS_GROUP_LEN])
        try:
            tmp_group.verify_group_integrity(force=True)
            tmp_group_info = tmp_group.get_group_info()
        except RDSIntegrityFailure as err:
            # print(err)
            continue  # It's not an RDS Group.  Quietly keep looking...
        except ValueError:
            break  # Ran out of bits
        else:
            if first_index is None:
                first_index = index
            if index > last_index:
                last_index = index
            if debug is True:
                print(f'Index "{index}" contains an RDS Group of PI Code '
                      f'"{tmp_group_info.pi_code}" and Group Type: {tmp_group_info.group_type}')
            collection.add_rds_group(tmp_group)
    last_index += RDS_GROUP_LEN
    if debug is True:
        print(f'Full RDS binary:\n{payload[first_index:last_index]}')

    # PRINT IT
    pic_strs = collection.fetch_pic_strs()
    if pic_strs:
        if debug is True:
            print(f'Found PI Codes in this sample!')
            for pic_str in pic_strs:
                print(f'\t{pic_str}')
            print()
        pic_bytes = collection.fetch_pic_bytes()
        for pic_byte in pic_bytes:
            rdspicodes = collection.fetch_rdspicode_obj(pi_code=pic_byte)
            act_num_groups = rdspicodes.count_rds_groups()
            print(f'PI Code:\t{sanitize_ascii(rdspicodes.get_pi_code_str())}\n'
                  f'Station Name:\t{sanitize_ascii(rdspicodes.get_station_name())}\n'
                  f'Radio Text:\t{sanitize_ascii(rdspicodes.get_radio_text())}\n\n')
        if debug is True:
            act_num_picodes = payload.count(pic_byte)
            print(f'\nRDS PI Codes Detected = Actual {act_num_picodes} / '
                  f'Expected {exp_num_picodes}: '
                  f'{calculate_success_rate(exp_num_groups, act_num_groups)}%')
            print(f'\nRDS Group Success Rate = Actual {act_num_groups} / '
                  f'Expected {exp_num_groups}: '
                  f'{calculate_success_rate(exp_num_groups, act_num_groups)}%')


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
        filt = MatchedFilter.NONE           # Matched filter (Not RRC?!)
        sps = 0                             # Samples per symbol
        samples = None                      # Samples read from the capture
        decimate = 1                        # Decimation (e.g., 1 to skip decimation)
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
            if arg_vals.debug:
                plot_welch_psd(samples=samples, sample_rate=sample_rate,
                               title='Welch Power Spectral Density (post-squelch)', now=False)

        # [?] Analyze the Spectrum
        # spect_analysis = analyze_spectrum(samples, sample_rate=sample_rate, max_peaks=2)

        # [?] Detect Signal
        if spect_analysis is not None:
            det_signal = detect_signal(analysis=spect_analysis, scheme=mod_scheme)

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
        # loop_band = 0.01  # Default value
        loop_band = 0.06   # Alone... 88% / 88%
        # Dialed in loop band and dampening factor...
        # damp_fact = 0.707  # Default value
        damp_fact = 0.6  # 90.5% / 90.5%
        # damp_fact = 0.55  # 90.5% / 90.5%
        # damp_fact = 0.4  # 90.5% / 90.5%
        # damp_fact = 0.35  # 90.5% / 90.5%
        # damp_fact = 0.303  # 90.5% / 90.5%
        # damp_fact = 0.3  # 90.5% / 90.5%
        # damp_fact = 0.25  # 90.5% / 90.5%
        # damp_fact = 0.202  # 90.5% / 90.5%
        # damp_fact = 0.2  # 90.5% / 90.5%
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
                                     symbol_rate=symbol_rate, carrier_recovery=carrier_recovery,
                                     filt=filt)
            # if arg_vals.debug:
            #     plot_time_domain(samples=metric, samp_rate=sample_rate,
            #                      title='Time Domain (Demod Step 1: Metrics)', now=False)
            #     plot_symbol_boundaries(real_wave=metric, sps=sps,
            #                            title='Symbol Boundaries (Demod Step 1: Metrics)', now=False)
            # Step 2 - Time Sync w/ Interpolation(?)
            # symbol_metrics = recover_clock_mm(metric, sps, interp=None)  # Do not interpolate
            symbol_metrics = recover_clock_mm(metric, sps, interp=16)  # Interp for better boundary
            # if arg_vals.debug:
            #     plot_time_domain(samples=symbol_metrics, samp_rate=sample_rate,
            #                      title='Time Domain (Demod Step 2: Symbol Metrics)', now=False)
            #     plot_symbol_boundaries(real_wave=symbol_metrics, sps=1,
            #                            title='Symbol Boundaries (Demod Step 2: Symbol Metrics)',
            #                            now=False)
            # Step 3 - Symbol Decisions
            binary = decide_symbols(symbol_metrics=symbol_metrics, sample_rate=sample_rate,
                                    symbol_rate=symbol_rate, carrier_recovery=carrier_recovery)
        if arg_vals.debug:
            print(f'Demod Final Step: {binary}')
        # [!] Step 4 - Differentially Decode
        binary = decode_differential_binary(binary)
        if arg_vals.debug:
            print(f'Differential Decoded Binary: {binary}')

        # [?] Frame Sync
        # There's no frame to sync to, as it were.  RDS streams and the receiver eventually
        # picks it up and decodes it.  No preamble.  Maybe, you could use the PI Code from Block A
        # as a syncword, but that will change depending on the RDS traffic.

        # TESTING!
        # binary = EXP_PAYLOAD  # Taken from the GNU Radio demod stored in the SigMF description

        # [!] Parse Payload
        # There may be 42 well-formed RDS Groups in the capture file referenced in the module
        # docstring but there's at least one more RDS Block which contains a PI Code.
        parse_rds_traffic(binary, exp_num_picodes=43, exp_num_groups=42, debug=arg_vals.debug)
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
