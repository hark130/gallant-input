"""This script utilizes GAIN and RXTX to implement, rx, and tx a custom protocol.

USAGE:

# Help
python rf_capstone_v3.py --help

# Same Machine, Two SDRs
uhd_find_devices
# Terminal 1
python rf_capstone_v3.py --serial 317650F --user 1
# Terminal 2
python rf_capstone_v3.py --serial 3512A99 --user 2

NOTES:
    - Include the following in the specification (not the user documentation):
        FSK deviation/separation      4.8 kHz
        estimated occupied bandwidth  9.6 kHz
        guard space                   4.8 kHz
        channel spacing               14.4 kHzs
"""


# Standard Imports
from collections import namedtuple
from dataclasses import dataclass, field
from typing import Final
import argparse
import random
import sys
import threading
import time
# Third Party Imports
from scipy import signal
import matplotlib.pyplot as plt
import numpy
import uhd
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.converters import (convert_ascii_to_bin_bytes, convert_bin_bytes_to_ascii,
                                      convert_bin_bytes_to_int, convert_bin_bytes_to_ndarray)
from gallant_input.filters import apply_fir, create_basic_lpf, design_lpf
from gallant_input.io import write_samples
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.modem import Modem
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modscheme import ModScheme
from gallant_input.plot import (plot_spectrum, plot_symbol_boundaries, plot_time_domain,
                                plot_welch_psd)
from gallant_input.gain_sigmf.sigmfmetabuilder import build_default_metadata
from gallant_input.radio.config_direction import ConfigDirection
from gallant_input.radio.gain_usrp import configure_usrp, receive, transmit
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.spacetime import create_rfc_3339_z_time
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm
from gallant_input.validation import validate_pos_float_or_int, validate_pos_int, validate_type
from rxtx.frame_receiver2 import FrameReceiver2  # Now with more checksumming
from rxtx.utilities import convert_field_val, evaluate_payload


CLI_ARG_DEBUG: Final[str] = 'debug'
CLI_ARG_FREQ: Final[str] = 'center_freq'
CLI_ARG_SERIAL: Final[str] = 'serial'
CLI_ARG_USER: Final[str] = 'user'


# DEBUGGING
DEBUG: Final[bool] = True  # In lieu of parsed args

# TXRX SPECIFICATIONS
# CENTER_FREQ: Final[float] = 912e6
# CENTER_FREQ: Final[float] = 911950e3  # TESTING
CENTER_FREQ: Final[float] = 912050e3  # TESTING
SAMPLE_RATE: Final[float] = 240e3
MAX_USERS: Final[int] = 2  # Currently only supports two users


# PROTOCOL SPECIFICATIONS
DATA_LEN_WIDTH: Final[int] = 8  # Fixed width of the data length field, in bits
CHECKSUM_WIDTH: Final[int] = 8  # Fixed width of the checksum filed, in bits
SYMBOL_RATE: Final[int] = 2400

# MESSAGES TO TRANSMIT
# MESSAGE 1: test
MSG1: Final[bytes] = convert_ascii_to_bin_bytes(message='test', clean_it=True)
# MESSAGE 2: abc123
MSG2: Final[bytes] = convert_ascii_to_bin_bytes(message='abc123', clean_it=True)
# MESSAGE 3: This is my test input.
MSG3: Final[bytes] = convert_ascii_to_bin_bytes(message='This is my test input.', clean_it=True)
# MESSAGE 4: This we'll defend
MSG4: Final[bytes] = convert_ascii_to_bin_bytes(message="This we'll defend", clean_it=True)
# MESSAGE 5: Now what do I do?
MSG5: Final[bytes] = convert_ascii_to_bin_bytes(message='Now what do I do?', clean_it=True)
# MESSAGE 6: 123 (with non-printable characters)
MSG6: Final[bytes] = convert_ascii_to_bin_bytes(message='1\n\t2\r\x00\x013', clean_it=False)
# MESSAGE 7: Lorem ipsum dolor sit amet, ___?  (used for DEBUG mode)
MSG7: Final[bytes] = convert_ascii_to_bin_bytes(message='Lorem ipsum dolor sit amet, ___?')
MESSAGES: Final[List] = [MSG1, MSG2, MSG3, MSG4, MSG5, MSG6, MSG7]

# PROTOCOL MACROS
PREAMBLE: Final[bytes] = 32 * b'10'
SYNCWORD: Final[bytes] = b'11011000110111000101000100101110'  # 0xD8DC512E
HEADER: Final[bytes] = PREAMBLE + SYNCWORD
DATA: Final[bytes] = MSG3  # UPDATE THIS WITH NEW DATA (see above)
DATA_LEN: Final[bytes] = convert_field_val(len(DATA) // 8, max_bit_len=DATA_LEN_WIDTH)
PAYLOAD: Final[bytes] = DATA_LEN + DATA
FRAME: Final[bytes] = HEADER + PAYLOAD  # Transmit this


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


def build_modem_config(sample_rate: float | int, symbol_rate: float | int,
                       freqs: UserFreqs) -> ModemConfig:
    """Build a ModemConfig child class object."""
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate,
                        freq0=freqs.f0, freq1=freqs.f1)
    return config


def build_frame(preamble: bytes, syncword: bytes, message: bytes) -> bytes:
    """Build a frame."""
    data_len = convert_field_val(len(message) // 8, max_bit_len=DATA_LEN_WIDTH)
    checksum = convert_field_val(generate_checksum(message), max_bit_len=CHECKSUM_WIDTH)
    header = preamble + syncword
    payload = data_len + message + checksum
    return header + payload


def build_usrp(serial: str) -> uhd.usrp.MultiUSRP:
    """Build the USRP object."""
    if serial:
        usrp = uhd.usrp.MultiUSRP('serial=' + serial)
    else:
        usrp = uhd.usrp.MultiUSRP("type=b200")
    return usrp


def calc_bandwidth(symbol_rate: int) -> int:
    """Calculate the bandwidth using Carson's Rule.

    Carson's Rule: Bt = freq_sep + (2 * Baud)
    """
    bandwidth = calc_freq_sep(symbol_rate) + (2 * symbol_rate)
    return bandwidth


def calc_freq_sep(symbol_rate: int) -> int:
    """Calculate the frequency separation."""
    freq_sep = 2 * symbol_rate
    return freq_sep


def calc_freqs(center_freq: float | int, user: int, symbol_rate: int) -> UserFreqs:
    """Calculate the user-specific center frequency, off freq, and on freq."""
    # LOCAL VARIABLES
    freq_sep = calc_freq_sep(symbol_rate)    # Frequency separation
    bandwidth = calc_bandwidth(symbol_rate)  # (Carson's Rule) Bt = freq_sep + (2 * Baud)
    freq0 = -(freq_sep / 2)                  # Off freq (User 1 default)
    freq1 = (freq_sep / 2)                   # On freq (User 1 default)
    new_center = 0.0                         # The user's new center freq
    channel_spacing = 0                      # Each channel needs this much room

    # INPUT VALIDATION
    validate_pos_float_or_int(center_freq, 'center_freq')
    _validate_user(user)
    validate_pos_int(symbol_rate, 'symbol_rate')

    # CALC FREQS
    channel_spacing = bandwidth + (2 * symbol_rate)
    if user == 1:
        new_center = center_freq - channel_spacing  # Shift user 1 left
    elif user == 2:
        new_center = center_freq + channel_spacing  # Shift user 2 right
    else:
        raise NotImplementedError(f'Unsupported number of users {user}')

    # DONE
    return UserFreqs(center=new_center, f0=freq0, f1=freq1)


def create_tailored_lpf(sample_rate: float | int, symbol_rate: int,
                        numtaps: int = 101) -> numpy.ndarray:
    """Create a LPF for the protocol using the channel bandwidth to determine the cutoff.

    Default cutoff values were allowing the transmit channel to 'leak' into the receive channel.
    """
    chan_bandwidth = calc_bandwidth(symbol_rate=symbol_rate)
    cutoff = round(chan_bandwidth, -3) / 2  # Round up to the nearest 1000s, centered
    print(f'SAMPLE RATE: {sample_rate} (fs/2 == {sample_rate/2})')  # DEBUGGING
    print(f'CUTOFF: {cutoff}')  # DEBUGGING
    taps = design_lpf(numtaps=numtaps, cutoff=cutoff, fs=sample_rate)
    return taps


def generate_checksum(data_field: bytes) -> int:
    """Generates an 8-bit checksum by adding, then ignoring the MSBits, all the byte values."""
    # print(f'HERE I AM WITH: {data_field}')  # DEBUGGING
    # print(f'THE SUM IS: {sum(data_field)}')  # DEBUGGING
    # print(f'RETURNING: {sum(data_field) & 0xFF}')  # DEBUGGING
    return sum(data_field) & 0xFF  # Mask off the MSBits


def parse_frame(frame: numpy.ndarray, modem: Modem) -> None:
    """Parse the frame by field instead of all at once."""
    header_len = len(PREAMBLE+SYNCWORD)  # Length of the header
    meta_len = header_len + 8            # Preamble + Syncword + Data Len
    metadata = modem.decide_symbols(symbol_metrics=frame[:meta_len])
    # print(f'RAW PREAMBLE + SYNCWORD + DATA LEN: {metadata}')  # DEBUGGING
    data_len = convert_bin_bytes_to_int(metadata[:8])
    # print(f'DATA LEN: {data_len}')  # DEBUGGING
    data = modem.decide_symbols(symbol_metrics=frame[meta_len:meta_len+(data_len)])
    # print(f'DATA: {data}')  # DEBUGGING
    print_message(data_field=data)


def parse_args() -> dict[str:Any]:
    """Parse the command line arguments.

    Returns:
        A dictionary of keys and their associataed values.
    """
    # LOCAL VARIABLES
    parser = None  # ArgumentParser object
    args = None    # Parsed argument Namespace

    # SETUP
    parser = argparse.ArgumentParser(prog='RF Captstone v3.0',
                                     description='Custom Bidirectional SDR Communication Protocol')
    # Debug mode
    parser.add_argument(f'-{CLI_ARG_DEBUG[0]}', f'--{CLI_ARG_DEBUG}', action='store_true',
                        default=False, required=False,
                        help='Enable verbose DEBUG print statements.')
    # Center frequency
    # parser.add_argument(f'-{CLI_ARG_FREQ[0]}', f'--{CLI_ARG_FREQ}', type=float,
    #                     action='store', help='Center frequency for communication', required=True)
    # SDR Serial Number
    parser.add_argument(f'-{CLI_ARG_SERIAL[0]}', f'--{CLI_ARG_SERIAL}', type=str,
                        action='store', help='Serial number of the desired device', required=False)
    # User
    parser.add_argument(f'-{CLI_ARG_USER[0]}', f'--{CLI_ARG_USER}', type=int,
                        action='store', help='Which user are you?',
                        required=True)

    # PARSE IT
    args = parser.parse_args()

    # DONE
    return _construct_arg_dict(args=args)


def print_message(data_field: bytes) -> None:
    """Print one data field."""
    message = convert_bin_bytes_to_ascii(data_field, clean_it=True)
    print(f'\n[RX] Received: {message}\n')


def receive_frames(usrp: uhd.usrp.multi_usrp.MultiUSRP, modem: Modem, preamble: numpy.ndarray,
                   syncword: numpy.ndarray, stop_event: threading.Event, debug: bool,
                   lpf: numpy.ndarray):
    """Capture an infinite number of frames (until stop_event triggers)."""
    print('[RX] Starting')
    sps = modem._sps  # Samples per symbol
    lpf = lpf  # Use the same taps to RX as to TX
    frame_receiver = FrameReceiver2(modem=modem, preamble=preamble, syncword=syncword,
                                    checksum=generate_checksum)
    stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
    stream_args.channels = [0]
    streamer = usrp.get_rx_stream(stream_args)
    buffer = numpy.empty((1, streamer.get_max_num_samps()), dtype=numpy.complex64)
    metadata = uhd.types.RXMetadata()
    received = numpy.empty(0, dtype=numpy.complex64)
    total = 0
    datum = []  # Data pulled from frames
    exp_data = MSG7 if debug is True else None  # Calculate and print BERs in DEBUG mode
    print(f'RECEIVE FRAME EXP DATA: {exp_data} (debug is {debug})')  # DEBUGGING

    # Start continuous RX.
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    try:
        modem.parse()  # Update the sps attribute
        while not stop_event.is_set():
            count = streamer.recv(buffer, metadata)
            if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                raise RuntimeError(f"RX error: {metadata.strerror()}")
            # print(f'[RX] Received {count} samples')  # DEBUGGING
            received = numpy.concatenate([received, buffer[0, :count]])  # Store it
            if len(received) > modem._sps * 1000:
                # print(f'[RX] Processing {len(received)} samples')  # DEBUGGING
                # Filter
                received = apply_fir(samples=received, coeffs=lpf)
                # Step 1 - Demod to Metrics
                metric = modem.demodulate_to_metric(samples=received)
                # Step 2 - Time Sync w/ Interpolation(?)
                # symbol_metrics = recover_clock_mm(metric, modem._sps,, interp=None)  # Do not interpolate
                symbol_metrics = recover_clock_mm(metric, modem._sps, interp=16)  # Interp for better boundary
                # Step 3 - Parse Frames
                datum = frame_receiver.process(symbol_metrics=symbol_metrics, exp_data=exp_data)
                for data in datum:
                    print_message(data_field=data)  # Print any messages
                received = numpy.empty(0, dtype=numpy.complex64)  # Empty the array
    finally:
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        streamer.issue_stream_cmd(stream_cmd)


def _construct_arg_dict(args: argparse.Namespace) -> dict[str:Any]:
    """Construct an ArgVals data class from the parsed args."""
    # LOCAL VARIABLES
    arg_dict = {}  # Dictionary of args and their values
    arg_keys = [CLI_ARG_DEBUG, CLI_ARG_FREQ, CLI_ARG_SERIAL, CLI_ARG_USER]

    # INPUT VALIDATION
    validate_type(var=args, var_name='args', var_type=argparse.Namespace)

    # GET IT
    for arg_key in arg_keys:
        arg_dict[arg_key] = _get_eafp_attr(args=args, attr=arg_key)

    # DONE
    return arg_dict


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


def _validate_user(user: int) -> None:
    """Validate a 'user' argument."""
    # INPUT VALIDATION
    validate_pos_int(user, 'user')
    if user > MAX_USERS:
        raise RuntimeError(f'Invalid number of users ({user}) for a maximum of {MAX_USERS}')


def main() -> None:
    """do_it()."""
    try:
        # LOCAL VARIABLES
        arg_dict = parse_args()                             # Read user input
        usrp = build_usrp(serial=arg_dict[CLI_ARG_SERIAL])  # Build the SDR object
        samp_rate = SAMPLE_RATE                             # Sample rate
        symb_rate = SYMBOL_RATE                             # Symbol rate
        # Calculate the new frequencies for both users
        comm_freqs = CommFreqs(user=arg_dict[CLI_ARG_USER], center_freq=CENTER_FREQ,
                               symbol_rate=symb_rate)
        our_freqs = comm_freqs.get_my_freqs()
        their_freqs = comm_freqs.get_user_freqs(2 if arg_dict[CLI_ARG_USER] == 1 else 1)
        print(f'OURS: {our_freqs}\nTHEIRS: {their_freqs}')  # DEBUGGING
        sps = calculate_sps(sample_rate=samp_rate, symbol_rate=symb_rate)
        rx_gain = 30                                        # RX gain
        tx_gain = 30                                        # TX gain
        channel = 0                                         # SDR channel
        # tx_samples = None    # An array of samples to transmit
        # rx_samples = None    # The received samples
        squelch_db = None    # Squelch threshold in db (e.g., -48, -55); skip w/ None
        # num_samples = 0      # Define this later after modulated samples are ready (len(samples) x 2?)
        modem_config = build_modem_config(sample_rate=samp_rate, symbol_rate=symb_rate,
                                          freqs=our_freqs)  # FSK2()'s demod doesn't use freqs
        modem = build_modem(config=modem_config)
        stop_event = threading.Event()                      # Signal the child thread to exit
        rx_thread = None                                    # The "receive" thread

        # SETUP
        lpf = create_tailored_lpf(sample_rate=samp_rate, symbol_rate=symb_rate)
        configure_usrp(usrp=usrp, samp_rate=samp_rate, center_freq=their_freqs.center,
                       gain=rx_gain, channel=channel, direction=ConfigDirection.RX)
        configure_usrp(usrp=usrp, samp_rate=samp_rate, center_freq=our_freqs.center,
                       gain=tx_gain, channel=channel, direction=ConfigDirection.TX)

        # RECEIVE
        # Start
        bipolar_preamble = convert_bin_bytes_to_ndarray(PREAMBLE, bipolar=True)
        syncword_arr = convert_bin_bytes_to_ndarray(SYNCWORD, bipolar=False)
        rx_thread = threading.Thread(
            target=receive_frames,
            args=(usrp, modem, bipolar_preamble, SYNCWORD, stop_event, arg_dict[CLI_ARG_DEBUG], lpf)
        )
        rx_thread.start()
        time.sleep(0.1)  # Give the receive thread a head starts

        # TRANSMIT
        try:
            while True:
                # Build the frame
                if arg_dict[CLI_ARG_DEBUG] is True:
                    tmp_msg = MSG7  # For calculating BER
                else:
                    tmp_msg = random.choice(MESSAGES)  # Choose a random message
                print(f'[TX] Sending - {convert_bin_bytes_to_ascii(tmp_msg, clean_it=True)}')
                tmp_frame = build_frame(preamble=PREAMBLE, syncword=SYNCWORD, message=tmp_msg)
                tx_samples = modem.modulate(bin_bytes=tmp_frame)
                # [?] Filter?
                tx_samples = apply_fir(samples=tx_samples, coeffs=lpf)
                transmit(usrp=usrp, samples=tx_samples)
                tmp_sleep = random.randint(1, 5)
                print(f'[TX] Sleeping - {tmp_sleep} secs')
                time.sleep(tmp_sleep)
        except KeyboardInterrupt:
            time.sleep(0.2)  # Let the receive thread finish?
            stop_event.set()  # Tell the receive thread to stop
            rx_thread.join()
            print()
    except (RuntimeError, LookupError, KeyError) as err:
        print(err)
        if 'No devices found' in err.args[0]:
            if arg_dict[CLI_ARG_DEBUG] is True:
                if arg_dict[CLI_ARG_SERIAL]:
                    print('\nDid you neglect to connect SDR serial number '
                          f'"{arg_dict[CLI_ARG_SERIAL]}"?  If not, it seems to be unavailable.  '
                          'Verify with `uhd_find_devices`.', file=sys.stderr)
                else:
                    print('\nThere are no devices available.  Either connect another SDR or '
                          f'use the --{CLI_ARG_SERIAL} CLI argument.', file=sys.stderr)
        raise err


if __name__ == '__main__':
    main()
    