"""Entry point."""

# Standard Imports
from typing import Final
import math
import sys
import threading
import time
# Third Party Imports
import numpy as np
from scipy.signal import firwin
# Local Imports
from protoroad.bpsk import BPSK
from protoroad.constants import BPSK_MAP, EXIT_FAIL, EXIT_SUCCESS, FEC_REPEATS, PREAMBLE, SYNCWORD
from protoroad.convert import (convert_bin_bytes_to_ascii, convert_bit_array_to_ascii,
                               convert_bit_array_to_bytes, convert_msg_to_binary)
from protoroad.frame import build_frame, build_header, build_payload
from protoroad.radio import Radio
from protoroad.signals import create_rrc_taps

DEBUG_SLEEP: Final[int | float] = 0.1  # A "tasteful" debug sleep
DEFAULT_RX_GAIN: Final[float] = 30.0  # RX gain (dB); B2xx range ~0-76
DEFAULT_TX_GAIN: Final[float] = 30.0  # TX gain (dB); B2xx range ~0-89.8; start low, raise as needed
LOG_STR_RX: Final[str] = "[RX] {action} - {message}"  # Receiver format string
LOG_STR_TX: Final[str] = "[TX] {action} - {message}"  # Transmit format string
PROTOCOL_ALPHA: Final[float] = 0.35  # Protocol roll-off factor: matched filter, bandwidth calc.
PROTOCOL_CENTER: Final[float] = 913_000_000  # Center frequency of the protocol
PROTOCOL_LO_OFFSET: Final[float] = 0  # Analog LO offset moves the DC spike out of band
# PROTOCOL_LO_OFFSET: Final[float] = 100_000  # Analog LO offset moves the DC spike out of band
# PROTOCOL_LO_OFFSET: Final[float] = 1_000_000  # Analog LO offset moves the DC spike out of band
PROTOCOL_SPS: Final[int] = 4  # The protocol's samples-per-symbol
PROTOCOL_BAUD: Final[int] = 250_000  # The protocol's symbol rate
PROTOCOL_SAMP_RATE: Final[int] = PROTOCOL_SPS * PROTOCOL_BAUD
TEST_MESSAGE: Final[bytes] = b"This is my test input.  Mine?!?!"  # 32 bytes of 'known' message
UNUSED_FIELD: Final[int] = 0xAA  # Value for unused 8-bit header fields


def calc_bandwidth(symbol_rate: int, alpha: float = PROTOCOL_ALPHA) -> float:
    """Occupied RF bandwidth of RRC-shaped linear modulation (e.g., BPSK).

    B = Rs * (1 + alpha).  Spectrum spans +/- B/2 around the carrier.
    """
    return symbol_rate * (1.0 + alpha)


def calc_lpf_cutoff(symbol_rate: int, alpha: float = PROTOCOL_ALPHA, max_offset_hz: float = 0,
                    margin_hz: float = 20_000) -> float:
    """Pre-AGC channel-select LPF cutoff (one-sided, baseband).

    The full RRC signal must make it through the filter even at worst-case frequency offset.
    The matched filter does the precise filtering.  Max offset of 0 Hz should be acceptable if
    frequency offset has already been corrected.

    NOTE: The margin_hz default value is a rule-of-thumb placeholder.  Verify it:
        1. Manually by...
            - plotting the frequency response with scipy.signal.freqz(lpf_taps, fs=SAMPLE_RATE)
            - verify the response is flat to within about 0.1 dB out to the signal edge plus offset
            - It’s down at least 40 dB by at the edge of the transition.
        2. Programmatically by...
            - designing the FIR with Parks-McClellan (scipy.signal.remez)
    """
    half_bw = calc_bandwidth(symbol_rate, alpha) / 2  # Half the bandwidth
    cutoff = half_bw + max_offset_hz + margin_hz      # Add up the buffer zones
    return math.ceil(cutoff / 1000) * 1000            # Round up to next kHz


def create_tailored_lpf(sample_rate: float, symbol_rate: int,
                        numtaps: int = 101) -> np.ndarray:
    """Create a LPF for the protocol."""
    cutoff = calc_lpf_cutoff(symbol_rate=symbol_rate)              # LPF cutoff
    return firwin(numtaps=numtaps, cutoff=cutoff, fs=sample_rate)  # LPF taps


def get_rrc_taps(sps: int, span: int = 11, alpha: float = PROTOCOL_ALPHA) -> np.ndarray:
    """Get the RRC matched filter taps for the protocol."""
    return create_rrc_taps(sps=sps, span=span, alpha=alpha)


def get_tx_msg() -> bytes:
    """Get a message to transmit."""
    return TEST_MESSAGE


def print_debug(radio: Radio) -> None:
    """Debug logging."""
    if radio:
        usrp, ch = radio.usrp, 0
        print("MCR      :", usrp.get_master_clock_rate())
        print("TX rate  :", usrp.get_tx_rate(ch))
        print("TX freq  :", usrp.get_tx_freq(ch))
        print("TX gain  :", usrp.get_tx_gain(ch), usrp.get_tx_gain_range(ch))
        print("TX ant   :", usrp.get_tx_antenna(ch), "of", usrp.get_tx_antennas(ch))
        print("TX bw    :", usrp.get_tx_bandwidth(ch))
        print("Shaped peak |x| (first frame) printed below")


def main() -> int:
    """do_it()."""
    # LOCAL VARIABLES
    exit_code = EXIT_SUCCESS                   # Exit status
    tx_sleep = DEBUG_SLEEP                     # A tasteful sleeep
    sdr_serial = "351B80B"                     # Choose serial number (351B80B or 352825E or None)
    rrc_taps = get_rrc_taps(sps=PROTOCOL_SPS)  # Matched filter taps
    stop_event = threading.Event()             # Signal the child thread to exit
    # Modulator/demodulator
    modem = BPSK(mapping=BPSK_MAP, samples_per_symbol=PROTOCOL_SPS, symbol_rate=PROTOCOL_BAUD)
    radio = Radio(samp_rate=PROTOCOL_SAMP_RATE, center_freq=PROTOCOL_CENTER,
                  rx_gain=DEFAULT_RX_GAIN, tx_gain=DEFAULT_TX_GAIN,
                  serial=sdr_serial, lo_offset=PROTOCOL_LO_OFFSET)

    # SETUP
    print_debug(radio=radio)  # DEBUGGING

    # START IT
    try:
        # Start listening thread
        # Start transmitting
        input(LOG_STR_TX.format(action="Ready", message="Press <ENTER> to start"))
        while True:
            try:
                tmp_msg = get_tx_msg()
                tmp_dat = build_payload(tmp_msg)
                tmp_hdr = build_header(dst=UNUSED_FIELD, src=UNUSED_FIELD, msg_type=UNUSED_FIELD,
                                       seq=UNUSED_FIELD, msg_len=len(tmp_msg))
                tmp_frame = build_frame(preamble=PREAMBLE, syncword=SYNCWORD, header=tmp_hdr,
                                        payload=tmp_dat, fec_repeats=FEC_REPEATS)
                tmp_samples = modem.modulate(binary=tmp_frame)
                tmp_shaped = np.convolve(tmp_samples, rrc_taps)
                print(LOG_STR_TX.format(action="Sending", message=tmp_msg))
                print(f"peak {np.abs(tmp_shaped).max()}")  # DEBUGGING
                tmp_sent = radio.transmit(samples=tmp_shaped)
                print(LOG_STR_TX.format(action="Sent",
                                        message=f"{tmp_sent} samples ({len(tmp_shaped)} + pad)"))
                if tx_sleep:
                    print(LOG_STR_TX.format(action="Sleeping", message=f"{tx_sleep} seconds"))
                    time.sleep(tx_sleep)
            except KeyboardInterrupt:
                time.sleep(0.2)  # Let the receive thread finish?
                stop_event.set()  # Tell the receive thread to stop
                # rx_thread.join()  # Wait for it
                print()
                break
    except (RuntimeError, LookupError, KeyError) as err:
        print(err)
        if 'No devices found' in err.args[0]:
                print(f"\nDid you neglect to connect SDR serial number {sdr_serial}?"
                      "If not, it seems to be unavailable.  "
                      "Verify with `uhd_find_devices`.", file=sys.stderr)
        else:
            print("\nThere are no devices available.", file=sys.stderr)
        exit_code = EXIT_FAIL
        raise err  # DEBUGGING

    # DONE
    return exit_code
