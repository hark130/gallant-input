"""Can I get this to work?"""


# Standard Imports
from typing import Final
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
from gallant_input.filters import apply_fir, create_basic_lpf
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
from gallant_input.radio.gain_usrp import configure_usrp, receive, transmit
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.spacetime import create_rfc_3339_z_time
from gallant_input.synch.frame import correlate_it, find_frame_start
from gallant_input.synch.timing import recover_clock_mm
from rxtx.utilities import convert_data_len, evaluate_payload


DEBUG: Final[bool] = True  # In lieu of parsed args
RECEIVE: Final[bool] = True  # SPOT for testing

# PROTOCOL SPECIFICATIONS
DATA_LEN_WIDTH: Final[int] = 8  # Fixed width of the data length field, in bits
SYMBOL_RATE: Final[int] = 2400

# MESSAGES TO TRANSMIT
# MESSAGE 1: test
MSG1: Final[bytes] = convert_ascii_to_bin_bytes(message='test', clean_it=True)
# MESSAGE 2: abc123
MSG2: Final[bytes] = convert_ascii_to_bin_bytes(message='abc123', clean_it=True)
# MESSAGE 3: This is my test input.
MSG3: Final[bytes] = convert_ascii_to_bin_bytes(message='This is my test input.', clean_it=True)

# PROTOCOL MACROS
PREAMBLE: Final[bytes] = 32 * b'10'
SYNCWORD: Final[bytes] = b'11011000110111000101000100101110'  # 0xD8DC512E
HEADER: Final[bytes] = PREAMBLE + SYNCWORD
DATA: Final[bytes] = MSG3  # UPDATE THIS WITH NEW DATA (see above)
DATA_LEN: Final[bytes] = convert_data_len(len(DATA) // 8, max_bit_len=DATA_LEN_WIDTH)
PAYLOAD: Final[bytes] = DATA_LEN + DATA
FRAME: Final[bytes] = HEADER + PAYLOAD  # Transmit this


def build_modem(config: ModemConfig) -> Modem:
    """Build a Modem child class object."""
    modem_obj = FSK2(config=config)
    return modem_obj


def build_modem_config(sample_rate: float | int, symbol_rate: float | int) -> ModemConfig:
    """Build a ModemConfig child class object."""
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate,
                        # freq0=-symbol_rate/2, freq1=symbol_rate/2)
                        freq0=-symbol_rate, freq1=symbol_rate)
    return config


def parse_payload(payload: bytes) -> None:
    """Parse and print the payload."""
    # PARSE IT
    data_len = convert_bin_bytes_to_int(payload[:8])
    message = convert_bin_bytes_to_ascii(payload[8:8+data_len], clean_it=True)

    # PRINT IT
    print(f'\nMESSAGE (LEN {data_len} BYTES): {message}\n')


def parse_frame(frame: numpy.ndarray, modem: Modem) -> None:
    """Parse the frame by field instead of all at once."""
    header_len = len(PREAMBLE+SYNCWORD)  # Length of the header
    meta_len = header_len + 8            # Preamble + Syncword + Data Len
    metadata = modem.decide_symbols(symbol_metrics=frame[:meta_len])
    print(f'RAW PREAMBLE + SYNCWORD + DATA LEN: {metadata}')  # DEBUGGINGs
    data_len = convert_bin_bytes_to_int(metadata[:8])
    print(f'DATA LEN: {data_len}')  # DEBUGGING
    data = modem.decide_symbols(symbol_metrics=frame[meta_len:meta_len+(data_len)])
    print(f'DATA: {data}')  # DEBUGGING
    message = convert_bin_bytes_to_ascii(data, clean_it=True)
    print(f'\nMESSAGE (LEN {data_len} BYTES): {message}\n')



def main() -> None:
    """do_it()."""
    # LOCAL VARIABLES
    usrp = uhd.usrp.MultiUSRP("type=b200")
    # center_freq = 411e6
    # center_freq = 911e6
    center_freq = 912e6
    samp_rate = 240e3
    symb_rate = SYMBOL_RATE
    sps = calculate_sps(sample_rate=samp_rate, symbol_rate=symb_rate)
    rx_gain = 40
    tx_gain = 50
    channel = 0
    tx_samples = None    # An array of samples to transmit
    rx_samples = None    # The received samples
    squelch_db = None    # Squelch threshold in db (e.g., -48, -55); skip w/ None
    # num_samples = 0      # Define this later after modulated samples are ready (len(samples) x 2?)
    modem_config = build_modem_config(sample_rate=samp_rate, symbol_rate=symb_rate)
    modem = build_modem(config=modem_config)
    received = {}        # Results of the "receive" thread
    stop_event = threading.Event()  # Signal the child thread to exit
    rx_thread = None     # The "receive" thread
    binary = b''         # Demodulated results

    # SETUP
    lpf = create_basic_lpf()
    configure_usrp(usrp=usrp, samp_rate=samp_rate, center_freq=center_freq,
                   rx_gain=rx_gain, tx_gain=tx_gain, channel=channel)
    tx_samples = modem.modulate(bin_bytes=FRAME)
    # num_samples = len(tx_samples) * 2
    # [?] Filter?
    # plot_time_domain(samples=tx_samples, samp_rate=samp_rate,
    #                  title='Time Domain (TX Samples before LPF)', now=False)
    # lpf = create_basic_lpf()
    tx_samples = apply_fir(samples=tx_samples, coeffs=lpf)
    # plot_time_domain(samples=tx_samples, samp_rate=samp_rate,
    #                  title='Time Domain (TX Samples after LPF)', now=True)

    # RECEIVE
    # Start
    rx_thread = threading.Thread(target=lambda: received.update(samples=receive(usrp, stop_event)))
    rx_thread.start()
    time.sleep(0.1)  # Give the receive thread a head starts

    # TRANSMIT
    transmit(usrp=usrp, samples=tx_samples)

    # PREPARE
    time.sleep(0.2)  # Let the receive thread finish?
    stop_event.set()  # Tell the receive thread to stop
    rx_thread.join()
    rx_samples = received["samples"]
    # [!] Filter!
    # plot_time_domain(samples=rx_samples, samp_rate=samp_rate,
    #                  title='Time Domain (RX Samples before LPF)', now=False)
    # lpf = create_basic_lpf()
    rx_samples = apply_fir(samples=rx_samples, coeffs=lpf)
    # plot_time_domain(samples=rx_samples, samp_rate=samp_rate,
    #                  title='Time Domain (RX Samples after LPF)', now=True)
    # [?] Squelch!
    # Identify noise floor
    if DEBUG:
        # plot_welch_psd(samples=rx_samples, sample_rate=samp_rate,
        #                title='Welch Power Spectral Density (pre-squelch)', now=False)
        # Squelch?
        if squelch_db is not None:
            rx_samples = squelch_signal(samples=rx_samples, threshold=squelch_db)
            # Squelch Results
            if DEBUG:
                plot_welch_psd(samples=rx_samples, sample_rate=samp_rate,
                               title='Welch Power Spectral Density (post-squelch)', now=True)

    # DEMOD
    # [?] Steps 1 - 3?
    # binary = modem.demodulate(samples=rx_samples)
    # -or-
    # [?] Step 1, 2, then 3!
    if not binary:
        # Step 1 - Demod to Metrics
        metric = modem.demodulate_to_metric(samples=rx_samples)
        if DEBUG:
            plot_time_domain(samples=metric, samp_rate=samp_rate,
                             title='Time Domain (Demod Step 1: Metrics)', now=False)
            plot_symbol_boundaries(real_wave=metric, sps=sps,
                                   title='Symbol Boundaries (Demod Step 1: Metrics)', now=False)
        # Step 2 - Time Sync w/ Interpolation(?)
        # symbol_metrics = recover_clock_mm(metric, sps, interp=None)  # Do not interpolate
        symbol_metrics = recover_clock_mm(metric, sps, interp=16)  # Interp for better boundary
        if DEBUG:
            plot_time_domain(samples=symbol_metrics, samp_rate=samp_rate,
                             title='Time Domain (Demod Step 2: Symbol Metrics)', now=False)
            plot_symbol_boundaries(real_wave=symbol_metrics, sps=1,
                                   title='Symbol Boundaries (Demod Step 2: Symbol Metrics)',
                                   now=False)
        # Step 2.5 - Frame Acquisition!
        frame_start = correlate_it(haystack=symbol_metrics, needle=PREAMBLE)
        # frame_start = correlate_it(haystack=symbol_metrics, needle=PREAMBLE+SYNCWORD)
        # print(f'correlate_it() THINKS THE FRAME STARTS AT INDEX {frame_start} (of {len(symbol_metrics)}) IN THE SYMBOL METRICS')
        frame_start = find_frame_start(symbol_metrics=symbol_metrics,
                                       preamble=convert_bin_bytes_to_ndarray(PREAMBLE, bipolar=True))
        # print(f'find_frame_start() THINKS THE FRAME STARTS AT INDEX {frame_start} (of {len(symbol_metrics)}) IN THE SYMBOL METRICS')
        symbol_metrics = symbol_metrics[frame_start:]
        # print(f'SLICED SYMBOL METRICS: {symbol_metrics[:40]}')  # DEBUGGING
        if DEBUG:
            plot_time_domain(samples=symbol_metrics, samp_rate=samp_rate,
                             title='Time Domain (Demod Step 2.5: Frame Acquisition)', now=False)
            plot_symbol_boundaries(real_wave=symbol_metrics, sps=1,
                                   title='Symbol Boundaries (Demod Step 2.5: Frame Acquisition)',
                                   now=False)
        # Step 3 - Symbol Decisions
        parse_frame(symbol_metrics, modem)
        exit()
        binary = modem.decide_symbols(symbol_metrics=symbol_metrics)
    if DEBUG:
        print(f'Demod Final Step: {binary}')

    # [?] Frame Sync
    needle = SYNCWORD
    index = correlate_it(binary, needle)
    payload = binary[index + len(needle):]

    plt.show()

    # [!] Parse Payload
    evaluate_payload(act_payload=payload, exp_payload=PAYLOAD, debug=DEBUG,
                     parse_payload=parse_payload)


if __name__ == '__main__':
    main()
    