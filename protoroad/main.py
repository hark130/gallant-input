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
from protoroad.burst_detector import detect_bursts
from protoroad.constants import BPSK_MAP, EXIT_FAIL, EXIT_SUCCESS, FEC_REPEATS, PREAMBLE, SYNCWORD
from protoroad.convert import (convert_bin_bytes_to_ascii, convert_bit_array_to_ascii,
                               convert_bit_array_to_bytes, convert_msg_to_binary)
from protoroad.frame import build_frame, build_header, build_payload, find_syncword, parse_frame
from protoroad.frame_info import FrameInfo, MsgType
from protoroad.plots import plot_burst_start
from protoroad.radio import Radio
from protoroad.signals import create_rrc_taps
from protoroad.timing_recovery import GardnerTimingRecovery

DEBUG_SLEEP: Final[int | float] = 0.1  # A "tasteful" debug sleep
# DEBUG_SLEEP: Final[int | float] = 0  # TESTING
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

####################################################################################################
#################### TEMPORARY IMPORTS TO SAVE IDEALIZED PACKETS TO SIGMF FILES ####################
####################################################################################################
from gallant_input.gain_sigmf.sigmfmetabuilder import build_default_metadata
from gallant_input.io import read_samples, write_samples
from gallant_input.spacetime import create_rfc_3339_z_time

RX_TEST_01: Final[str] = "./data/protoroad_01_s1M_b250k_ideal_frame.sigmf-data"
RX_TEST_02: Final[str] = "./data/protoroad_02_s1M_b250k_shaped_frame.sigmf-data"
RX_TEST_03: Final[str] = "./data/protoroad_03_s1M_b250k_ota_one_msg.sigmf-data"


def diagnose(samples: np.ndarray, modem: BPSK, rrc_taps: np.ndarray, sps: int) -> None:
    """Try coarse frequency correction + every sampling phase on one capture."""
    samples = samples - np.mean(samples)                      # Crude DC removal
    sq = samples ** 2                                         # BPSK squared -> tone at 2*df
    nfft = 1 << 18
    spec = np.abs(np.fft.fftshift(np.fft.fft(sq, nfft)))
    freqs = np.fft.fftshift(np.fft.fftfreq(nfft, d=1 / PROTOCOL_SAMP_RATE))
    offset = freqs[np.argmax(spec)] / 2
    print(f"Estimated frequency offset: {offset:.0f} Hz")
    for label, freq in (("uncorrected", 0.0), ("corrected", offset)):
        n = np.arange(samples.size)
        fixed = samples * np.exp(-2j * np.pi * freq * n / PROTOCOL_SAMP_RATE)
        filtered = np.convolve(fixed, rrc_taps)
        for phase in range(sps):
            bits = convert_bit_array_to_bytes(modem.demodulate(filtered[phase::sps]))
            match = find_syncword(bits, SYNCWORD)
            frame = parse_frame(bits, SYNCWORD, FEC_REPEATS)
            print(f"{label:11} phase {phase}: sync {match}, frame {frame is not None}")


def print_ndarray_details(array: np.ndarray, num_samps: int = 5, title: str = '') -> None:
    """Inspect an ndarray."""
    details = f"Shape: {array.shape} | Type: {array.dtype} | Real/Complex: {array.dtype.kind}: " \
              f"Samples: {array[:num_samps]}"
    if title:
        details = f"{title} - {details}"
    print(details)

def write_it(samp_rate: float, center_freq: float, filename: str, samples: np.ndarray,
             description: str) -> None:
    """Write some samples to a SigMF file."""
    date_time = create_rfc_3339_z_time()
    meta_data = build_default_metadata(samp_rate=samp_rate, date_time=date_time,
                                       center_freq=center_freq, description=description)
    write_samples(filename=filename, samples=samples, metadata=meta_data, overwrite=True)


def test_ideal(modem: BPSK, rrc_taps: np.ndarray, sps: int, fec_repeats: int) -> None:
    """Matched filter -> ideal downsample -> demodulate -> parse.  Simulation only."""
    samples = read_samples(filename=RX_TEST_02, sigmf_data=True)
    # print(f"SAMPLES: {samples}")  # DEBUGGING
    filtered = np.convolve(samples, rrc_taps)  # RX matched filter
    # print_ndarray_details(filtered)  # DEBUGGING
    # print(f"FILTERED: {filtered}")  # DEBUGGING
    symbols = filtered[len(rrc_taps) - 1::sps]  # Stand-in for timing recovery
    # print_ndarray_details(symbols)  # DEBUGGING
    bit_array = modem.demodulate(symbols)
    # print_ndarray_details(bit_array)  # DEBUGGING
    bits = convert_bit_array_to_bytes(bit_array)
    # print(f"BITS: {bits}")  # DEBUGGING
    frameinfo = parse_frame(bits, SYNCWORD, fec_repeats)
    print_frame(frameinfo=frameinfo, print_all=True)
    if frameinfo is None:
        diagnose(samples=samples, modem=modem, rrc_taps=rrc_taps, sps=sps)


def test_ota(filename: str, modem: BPSK, rrc_taps: np.ndarray, sps: int, fec_repeats: int) -> None:
    """Matched filter -> ideal downsample -> demodulate -> parse.  Simulation only."""
    samples = read_samples(filename=filename, sigmf_data=True)
    # print(f"SAMPLES: {samples}")  # DEBUGGING
    # print(f"AMP: {np.sqrt(np.mean(np.abs(samples) ** 2))}")  # DEBUGGING
    filtered = np.convolve(samples, rrc_taps)  # RX matched filter
    print_ndarray_details(filtered, title="Filtered")  # DEBUGGING
    # print(f"FILTERED: {filtered}")  # DEBUGGING
    bursts = detect_bursts(filtered, min_len=2_000)
    burst = bursts[0].samples     # Just the burst, no noise gaps
    burst = burst / np.sqrt(np.mean(np.abs(burst) ** 2))          # TEMPORARY stand-in for AGC
    print_ndarray_details(burst, title="Burst")  # DEBUGGING
    ted = GardnerTimingRecovery(sps=sps)
    symbols = ted.process(samples=burst)
    print_ndarray_details(symbols, title="Symbols")  # DEBUGGING
    bit_array = modem.demodulate(symbols)
    # print_ndarray_details(bit_array)  # DEBUGGING
    bits = convert_bit_array_to_bytes(bit_array)
    # print(f"BITS: {bits}")  # DEBUGGING
    frameinfo = parse_frame(bits, SYNCWORD, fec_repeats)
    print_frame(frameinfo=frameinfo, print_all=True)
    if frameinfo is None:
        diagnose(samples=samples, modem=modem, rrc_taps=rrc_taps, sps=sps)
    plot_burst_start(filtered, bursts[0], timing=ted, sync_index=61, sps=PROTOCOL_SPS)


####################################################################################################
####################################################################################################
####################################################################################################


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


def print_frame(frameinfo: FrameInfo, print_all: bool = False) -> None:
    """Print contents of frameinfo as appropriate."""
    if frameinfo is not None:
        if print_all is True:
            print(f"DESTINATION:  {frameinfo.dst}")
            print(f"SOURCE:       {frameinfo.src}")
            print(f"MESSAGE TYPE: {frameinfo.msg_type}")
            print(f"SEQUENCE NUM: {frameinfo.seq}")
        print(f"PAYLOAD:      {frameinfo.payload}")
    else:
        print("No frame to print?!")


def main() -> int:
    """do_it()."""
    # LOCAL VARIABLES
    exit_code = EXIT_SUCCESS                   # Exit status
    tx_sleep = DEBUG_SLEEP                     # A tasteful sleeep
    sdr_serial = "351B80B"                     # Choose serial number (351B80B or 352825E or None)
    rrc_taps = get_rrc_taps(sps=PROTOCOL_SPS)  # Matched filter taps
    stop_event = threading.Event()             # Signal the child thread to exit
    radio = None                               # Radio() object
    # Modulator/demodulator
    modem = BPSK(mapping=BPSK_MAP, samples_per_symbol=PROTOCOL_SPS, symbol_rate=PROTOCOL_BAUD)

    # TESTING
    # test_ideal(modem=modem, rrc_taps=rrc_taps, sps=PROTOCOL_SPS, fec_repeats=FEC_REPEATS)
    test_ota(filename=RX_TEST_03, modem=modem, rrc_taps=rrc_taps, sps=PROTOCOL_SPS,
             fec_repeats=FEC_REPEATS)
    return exit_code  # TESTING

    # DO IT
    try:
        # SETUP
        radio = Radio(samp_rate=PROTOCOL_SAMP_RATE, center_freq=PROTOCOL_CENTER,
                      rx_gain=DEFAULT_RX_GAIN, tx_gain=DEFAULT_TX_GAIN,
                      serial=sdr_serial, lo_offset=PROTOCOL_LO_OFFSET)
        print_debug(radio=radio)  # DEBUGGING

        # HEY, LISTEN!
        # Start listening thread

        # TRANSMIT
        # Start transmitting
        input(LOG_STR_TX.format(action="Ready", message="Press <ENTER> to start"))
        while True:
            try:
                tmp_msg = get_tx_msg()
                tmp_dat = build_payload(tmp_msg)
                tmp_hdr = build_header(dst=UNUSED_FIELD, src=UNUSED_FIELD, msg_type=MsgType.UNUSED,
                                       seq=UNUSED_FIELD, msg_len=len(tmp_msg))
                tmp_frame = build_frame(preamble=PREAMBLE, syncword=SYNCWORD, header=tmp_hdr,
                                        payload=tmp_dat, fec_repeats=FEC_REPEATS)
                tmp_samples = modem.modulate(binary=tmp_frame)
                # print(f"TMP FRAME: {tmp_frame}")  # DEBUGGING
                # write_it(samp_rate=PROTOCOL_SAMP_RATE, center_freq=PROTOCOL_CENTER * 1.0,
                #          filename=RX_TEST_01, samples=tmp_samples,
                #          description=tmp_frame.decode("ascii"))  # TESTING
                tmp_shaped = np.convolve(tmp_samples, rrc_taps)
                # write_it(samp_rate=PROTOCOL_SAMP_RATE, center_freq=PROTOCOL_CENTER * 1.0,
                #          filename=RX_TEST_02, samples=tmp_shaped,
                #          description=tmp_frame.decode("ascii"))  # TESTING
                # break  # TESTING
                print(LOG_STR_TX.format(action="Sending", message=tmp_msg))
                # print(f"peak {np.abs(tmp_shaped).max()}")  # DEBUGGING
                tmp_sent = radio.transmit(samples=tmp_shaped)
                print(LOG_STR_TX.format(action="Sent",
                                        message=f"{tmp_sent} samples ({len(tmp_shaped)} + pad)"))
                if tx_sleep:
                    print(LOG_STR_TX.format(action="Sleeping", message=f"{tx_sleep} seconds"))
                    time.sleep(tx_sleep)
                # break  # TESTING
            except KeyboardInterrupt:
                time.sleep(0.2)  # Let the receive thread finish?
                stop_event.set()  # Tell the receive thread to stop
                # rx_thread.join()  # Wait for it
                print()
                break
    except (RuntimeError, LookupError, KeyError) as err:
        print(err)
        if 'No devices found'.lower() in str(err).lower():
                print(f"\nDid you neglect to connect SDR serial number {sdr_serial}?"
                      "If not, it seems to be unavailable.  "
                      "Verify with `uhd_find_devices`.", file=sys.stderr)
        exit_code = EXIT_FAIL
        raise err  # DEBUGGING

    # DONE
    return exit_code
