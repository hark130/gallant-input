"""Intended as static receiver to DEBUG TX samples from the RF Capstone.

7. Run the module w/ --debug:
    - fiddle with main() variables (e.g., decimate, squelch_db)
    - disable unwanted plots
    - etc.

Example Usage:
    python -m rxtx.static_rx_rf_capstone --help
    python -m rxtx.static_rx_rf_capstone --baud 2400 --filename ./test/test_input/rf_capstone_raw_cap_c912p0644m_s240k_b2400.sigmf-data
    python -m rxtx.static_rx_rf_capstone --baud 2400 --filename ./test/test_input/rf_capstone_raw_cap_c912p0644m_s240k_b2400_one_message.sigmf-data
    python -m rxtx.static_rx_rf_capstone --baud 2400 --filename ./test/test_input/rf_capstone_raw_cap_c912p0644m_s240k_b2400_one_message_shortened.complex --samprate 240000
"""

# Standard Imports
from collections import namedtuple
from typing import Final
import sys
# Third Party Imports
import matplotlib.pyplot as plt
import numpy
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.converters import convert_bin_bytes_to_ascii, convert_bin_bytes_to_int
from gallant_input.filters import apply_fir, create_basic_lpf, design_lpf
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modem.modem import Modem
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.modscheme import ModScheme
from gallant_input.plot import (plot_spectrum, plot_symbol_boundaries, plot_time_domain,
                                plot_welch_psd)
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm
from rxtx.arg_parser import parse_args, print_help
from rxtx.utilities import decode_fec_repetition, evaluate_payload, get_filename, get_sample_rate

DEF_PREAMBLE: Final[bytes] = 32 * b'10'
DEF_SYNCWORD: Final[bytes] = b'11011000110111000101000100101110'  # 0xD8DC512E
DEF_PREAMWRD: Final[bytes] = DEF_PREAMBLE[-8:] + DEF_SYNCWORD  # Some preamble + sw (if necessary?)
EXP_PAYLOAD: Final[bytes] = b'0110000000011100000011111100000000011111100011111111111100011111' \
                            b'1111000000111000000111111000000111000111000111111000111111000111' \
                            b'0000001110000000000000000001111110001110000001110001111111110000' \
                            b'0000000000011111111100000011111100011111111100011100011100011111' \
                            b'1000111111000111000000111000000000000000000111111000000111000000' \
                            b'0001111110001111111111110001111110001111110000000001111110001111' \
                            b'1111111100011111111100000011100000000011100000000000000000011111' \
                            b'1111000000111111000111111000111000000111000111111111000111000000' \
                            b'0000001110000000000000000001111110000000000001110001111110001111' \
                            b'1100011100011111100000011100011100011111111100011100000000000011' \
                            b'1000111111000000000000111000000000000000000111000111111111111111' \
                            b'0001110001111111111111110001110001111111111111110000001111111111' \
                            b'1111111110000000'  # --debug message


# PROTOCOL SPECIFICATIONS
DATA_LEN_WIDTH: Final[int] = 8         # Fixed width of the data length field, in bits
CHECKSUM_WIDTH: Final[int] = 8         # Fixed width of the checksum filed, in bits
FEC_REPEAT: Final[int | None] = 3      # Forward Error Correction (FEC) repeat value


# Each user sends on theirs but receives on the other user's
UserFreqs = namedtuple('UserFreqs', ['center', 'f0', 'f1'])


class CommFreqs():
    """Dataclass containing user frequencies."""

    def __init__(self, user: int, center_freq: float | int, symbol_rate: int):
        """Class ctor.

        Arg:
            user:  sThis customer's user number.
        """
        self._user = user
        self._center_freq = center_freq
        self._symbol_rate = symbol_rate

    def get_my_freqs(self) -> UserFreqs:
        """Get the frequencies for this user."""
        return self.get_user_freqs(user=self._user)

    def get_user_freqs(self, user: int) -> UserFreqs:
        """Get the frequencies for a particular user."""
        return calc_freqs(center_freq=self._center_freq, user=user,
                          symbol_rate=self._symbol_rate)


def build_modem(config: ModemConfig) -> Modem:
    """Build a Modem child class object."""
    modem_obj = FSK2(config=config)
    return modem_obj


def build_modem_config(sample_rate: float | int, symbol_rate: float | int, freqs: UserFreqs) -> ModemConfig:
    """Build a ModemConfig child class object."""
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate,
                        freq0=freqs.f0, freq1=freqs.f1)
    return config


def generate_checksum(data_field: bytes) -> int:
    """Generates an 8-bit checksum by adding, then ignoring the MSBits, all the byte values."""
    return sum(data_field) & 0xFF  # Mask off the MSBits


def parse_payload(payload: bytes) -> None:
    """Parse and print the payload."""
    # LOCAL VARIABLES
    data_len = 0          # DATA LEN
    raw_data = b''        # FEC repeats included in this raw DATA field value
    data = b''            # Original data
    exp_check_bits = b''  # The CHECKSUM field
    exp_checksum = 0      # Checksum value converted from the CHECKSUM field
    act_checksum = 0      # Re-calculate the checksum from the data (*not* DATA)
    message = ''          # The original message

    # PARSE IT
    data_len = convert_bin_bytes_to_int(payload[:DATA_LEN_WIDTH]) * 8  # Length of the data
    # print(f'DATA LEN: {data_len}')  # DEBUGGING
    raw_data = payload[DATA_LEN_WIDTH:DATA_LEN_WIDTH + data_len]
    data = decode_fec_repetition(raw_data, FEC_REPEAT, force_odd=False)
    exp_check_bits = payload[DATA_LEN_WIDTH + data_len:DATA_LEN_WIDTH + data_len + CHECKSUM_WIDTH]
    if exp_check_bits:
        exp_checksum = convert_bin_bytes_to_int(binary=exp_check_bits)
    else:
        print(f'The CHECKSUM field was missing?!')
    act_checksum = generate_checksum(data_field=data)
    message = convert_bin_bytes_to_ascii(data)

    # PRINT IT
    if act_checksum != exp_checksum:
        print(f'[STATIC RX] Failed checksum (exp={exp_checksum}, act={act_checksum}, '
              f'checksum_bits={exp_check_bits}, '
              f'len_raw_data={len(raw_data)}, len_exp_data={data_len}, '
              f'decoded_data={data})')
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
        taps = None                         # LPF
        decimate = 1                        # Decimation (e.g., 1 to skip decimation)
        squelch_db = None                   # Squelch threshold in db (e.g., -48, -55); skip w/ None
        mod_scheme = ModScheme.FSK2         # Communicates anticipated modulation to detect_signal()
        spect_analysis = None               # SpectrumAnalysis obj
        det_signal = None                   # DetectedSignal obj
        metric = None                       # Step 1 - Continuous symbol metric at orig. sample rate
        symbol_metrics = None               # Step 2 - Recovered symbol metric for each orig. symbol
        binary = b''                        # Step 3 - Demodulated binary
        needle = b''                        # The needle being correlated to the package (e.g., sw)
        index = 0                           # Correlated index into the binary
        payload = b''                       # Frame synch'd binary
        modem_config = None                 # ModemConfig() object (build latest)
        modem = None                        # Modem() object (build latest)
        # HARD CODED FREQS
        user1_freqs = UserFreqs(center=912064400.0, f0=-2400.0, f1=2400.0)
        user2_freqs = UserFreqs(center=912035600.0, f0=-2400.0, f1=2400.0)

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
        # Filter!
        # if arg_vals.debug:
        #     plot_time_domain(samples=samples, samp_rate=sample_rate,
        #                      title='Time Domain (pre-filter)', now=False)
        #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
        #                   convert_db=True, center_freq=None,
        #                   title='Magnitude Spectrum (pre-filter)', now=False)
        taps = design_lpf(numtaps=101, cutoff=5000.0, fs=float(sample_rate))  # Replicated from rf_capstone
        samples = apply_fir(samples=samples, coeffs=taps)
        # if arg_vals.debug:
        #     plot_time_domain(samples=samples, samp_rate=sample_rate,
        #                      title='Time Domain (post-filter)', now=False)
        #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
        #                   convert_db=True, center_freq=None,
        #                   title='Magnitude Spectrum (post-filter)', now=False)

        # Decimate!
        if decimate > 1:
            samples = decimate_samples(samples=samples, decimate=decimate)
            sample_rate = sample_rate / decimate  # Update the sample rate
            sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Calc new sps
        if sps > 20 and arg_vals.debug:
            print(f'Consider decimating the samples-per-symbol, currently "{sps}", below 20')
        if arg_vals.debug and decimate > 1:
            plot_time_domain(samples=samples, samp_rate=sample_rate,
                             title='Time Domain (post-decimation)', now=False)
            plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
                          convert_db=True, center_freq=None,
                          title='Magnitude Spectrum (post-decimation)', now=False)

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
        spect_analysis = analyze_spectrum(samples, sample_rate=sample_rate, max_peaks=2)
        # print(f'SPECTRUM ANALYSIS: {spect_analysis}')  # DEBUGGING

        # [?] Detect Signal
        if spect_analysis is not None:
            det_signal = detect_signal(analysis=spect_analysis, scheme=mod_scheme)
            # print(f'DETECTED SIGNAL: {det_signal}')  # DEBUGGING

        # [?] Downconvert
        if det_signal is not None:
            if det_signal.center_frequency > 0 or det_signal.center_frequency < 0:
                print(f'Downconverting to {det_signal.center_frequency}Hz')
                samples = downconvert_signal(samples=samples, sample_rate=sample_rate,
                                             center_freq=det_signal.center_frequency)
                # if arg_vals.debug:
                #     plot_spectrum(samples=samples, samp_rate=sample_rate, shift_result=True,
                #                   convert_db=True, center_freq=None,
                #                   title='Magnitude Spectrum (post-baseband translation)', now=False)

        # DEMOD
        modem_config = build_modem_config(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                          freqs=user1_freqs)
        modem = build_modem(config=modem_config)
        # [?] Steps 1 - 3?
        # binary = modem.demodulate(samples=samples)
        # -or-
        # [?] Step 1, 2, then 3!
        if not binary:
            # Step 1 - Demod to Metrics
            metric = modem.demodulate_to_metric(samples=samples)
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
            binary = modem.decide_symbols(symbol_metrics=symbol_metrics)
        if arg_vals.debug:
            print(f'Demod Final Step: {binary}')

        # [?] Frame Sync
        needle = DEF_SYNCWORD
        index = correlate_it(binary, needle)
        # print(f'The needle {needle} was found at Index {index}')  # DEBUGGING
        payload = binary[index + len(needle):]
        print(f'Payload length: {len(payload)}')

        # [!] Parse Payload
        parse_payload(payload)
        # Use evaluate_payload() for the --debug message
        evaluate_payload(act_payload=payload, exp_payload=EXP_PAYLOAD, debug=arg_vals.debug,
                         parse_payload=parse_payload)
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
