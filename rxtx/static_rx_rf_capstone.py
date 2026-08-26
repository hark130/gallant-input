"""Intended as static receiver to DEBUG TX samples from the RF Capstone.

7. Run the module w/ --debug:
    - fiddle with main() variables (e.g., decimate, squelch_db)
    - disable unwanted plots
    - etc.

Example Usage:
    python -m rxtx.static_rx_rf_capstone --help
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
from gallant_input.converters import convert_bin_bytes_to_ascii
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
from rxtx.utilities import evaluate_payload, get_filename, get_sample_rate

DEF_PREAMBLE: Final[bytes] = 32 * b'10'
DEF_SYNCWORD: Final[bytes] = b'11011000110111000101000100101110'  # 0xD8DC512E
DEF_PREAMWRD: Final[bytes] = DEF_PREAMBLE[-8:] + DEF_SYNCWORD  # Some preamble + sw (if necessary?)
EXP_PAYLOAD: Final[bytes] = b'PAYLOADS ARE VARIABLE'  # Expected payload


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
    # PARSE IT
    data_len = convert_bin_bytes_to_int(payload[:DATA_LEN_WIDTH])  # Length of the data
    raw_data = payload[DATA_LEN_WIDTH:DATA_LEN_WIDTH + data_len]
    data = decode_fec_repetition(raw_data, FEC_REPEAT, force_odd=False)
    exp_check_bits = payload[DATA_LEN_WIDTH + data_len:DATA_LEN_WIDTH + data_len + CHECKSUM_WIDTH]
    exp_checksum = convert_bin_bytes_to_int(binary=exp_check_bits)
    act_checksum = generate_checksum(data_field=data)
    message = convert_bin_bytes_to_ascii(data)

    # PRINT IT
    if act_checksum != exp_checksum:
        print(f'[STATIC RX] Failed checksum (exp={exp_checksum}, act={act_checksum}, '
              f'checksum_bits={exp_check_bits}, data_bits_required={data_bits_required}, '
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
        if sps > 20 and arg_vals.debug:
            print(f'Consider decimating the samples-per-symbol, currently "{sps}", below 20')
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
        # [?] Steps 1 - 3?
        binary = demodulate(samples=samples, sample_rate=sample_rate, symbol_rate=symbol_rate)
        # -or-
        # [?] Step 1, 2, then 3!
        if not binary:
            # Step 1 - Demod to Metrics
            metric = demod_to_metric(samples=samples, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate)
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
