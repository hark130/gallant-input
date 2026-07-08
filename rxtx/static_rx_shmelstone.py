"""Born from my shmelstone_receiver and refactored to escape CPT Fox Time (CFT).

Example Usage:
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_hark1.sigmf-data
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_msg1_max.sigmf-data
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_msg2_long.sigmf-data
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_msg3_med.sigmf-data
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
from gallant_input.converters import convert_bin_bytes_to_ascii, convert_bin_bytes_to_int
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modscheme import ModScheme
from gallant_input.signal import (decimate_samples, detect_signal, downconvert_signal,
                                  squelch_signal)
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm

DEF_SAMP_RATE: Final[int] = 2400000
DEF_SYMB_RATE: Final[int] = 2400
DEF_PREAMBLE: Final[bytes] = b'01' * 32
DEF_SYNCWORD: Final[bytes] = b'11010011100100011101001110010001'  # 0xD391 0xD391
DEF_PREAMWRD: Final[bytes] = DEF_PREAMBLE[-8:] + DEF_SYNCWORD  # Some preamble + sw


def demod_to_bytes_full(samples: numpy.ndarray, sample_rate: float | int,
                        symbol_rate: float | int) -> bytes:
    """Demodulate a signal to binary bytes."""
    # LOCAL VARIABLES
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate, freq0=0, freq1=0)
    modem = None     # The demodulator class
    bin_bytes = b''  # The demodulated binary

    # DEMODULATE IT
    config.set_demod()  # Demodulate only
    modem = FSK2(config=config)
    bin_bytes = modem.demodulate(samples=samples)

    # DONE
    return bin_bytes


def demod_to_bytes_partial(real_wave: numpy.ndarray, sample_rate: float | int,
                           symbol_rate: float | int) -> bytes:
    """Demodulate a real waveform to binary bytes."""
    # LOCAL VARIABLES
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate, freq0=0, freq1=0)
    modem = None     # The demodulator class
    bin_bytes = b''  # The demodulated binary

    # DEMODULATE IT
    config.set_demod()  # Demodulate only
    modem = FSK2(config=config)
    bin_bytes = modem.demodulate_to_bytes(real_wave=real_wave)

    # DONE
    return bin_bytes


def demod_to_waveform(samples: numpy.ndarray, sample_rate: float | int,
                      symbol_rate: float | int) -> numpy.ndarray:
    """Demodulate a signal to a real waveform."""
    # LOCAL VARIABLES
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate, freq0=0, freq1=0)
    modem = None     # The demodulator class
    waveform = None  # The demodulated real waveform

    # DEMODULATE IT
    config.set_demod()  # Demodulate only
    modem = FSK2(config=config)
    waveform = modem.demodulate_to_samples(samples=samples)

    # DONE
    return waveform


def get_filename() -> Path:
    """In lieu of an actual argument parser, just get the filename."""
    # LOCAL VARIABLES
    arg_val = None   # argv[1]
    filename = None  # argv[1] as a Path object

    # GET IT
    try:
        arg_val = sys.argv[1]
    except IndexError as err:
        print_help()
        raise err from err
    filename = Path(arg_val)

    # DONE
    return filename


def parse_payload(payload: bytes) -> None:
    """Parse and print the payload."""
    # PARSE IT
    msg_len = convert_bin_bytes_to_int(payload[:8])                                       # Length
    msg_type = convert_bin_bytes_to_int(payload[8:16])                                    # Msg type
    user_len = convert_bin_bytes_to_int(payload[16:24])                                   # Name len
    user_name = convert_bin_bytes_to_ascii(payload[24:24 + (user_len * 8)])               # Username
    message = convert_bin_bytes_to_ascii(payload[24 + (user_len * 8):(msg_len + 1) * 8])  # Message

    # PRINT IT
    print(f'User "{user_name}" sent message type {msg_type}: {message}')


def print_help() -> None:
    """Print a help message."""
    # command_name [options/flags] <required_argument>
    print(f'\n\nUSAGE: {sys.argv[0]} <SIGMF FILENAME>\n\n', file=sys.stderr)


# pylint: disable=too-many-locals
def main() -> None:
    """do_it()."""
    try:
        # LOCAL VARIABLES
        sig_meta_parser = None            # The SigMFMetaParser (if filepath is a SigMF file)
        sample_rate = DEF_SAMP_RATE       # Capture sample rate
        symbol_rate = DEF_SYMB_RATE       # Capture symbol rate
        sps = 0                           # Samples per symbol
        filepath = get_filename()         # CLI capture file
        samples = read_samples(filepath)  # Samples read from the capture
        translated = samples              # Downshifted samples to 0 Hz center frequency
        squelch_db = -48                  # Squelch threshold in db
        spect_analysis = None             # SpectrumAnalysis obj
        det_signal = None                 # DetectedSignal obj
        binary = b''                      # Demodulated binary
        waveform = None                   # Demodulated real waveform
        index = 0                         # Correlated index
        new_binary = b''                  # Frame synch'd binary
        decimate = 20                     # Decimation

        # PREPARE
        # [ ] Get Samples
        # Fetch SigMF metadata (if available)
        if filepath.suffix.lower() == f'.{SIGMF_DATA_FILE_EXT}'.lower():
            sig_meta_parser = SigMFMetaParser(filepath.with_suffix(f'.{SIGMF_META_FILE_EXT}'))
            sample_rate = sig_meta_parser.get_sample_rate()

        # [ ] Clean Up
        # Decimate!
        samples = decimate_samples(samples=samples, decimate=decimate)
        sample_rate = sample_rate / decimate
        sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Calc the sps

        # [ ] Squelch!
        samples = squelch_signal(samples=samples, threshold=squelch_db)  # -48 is the sweet spot

        # [ ] Analyze the Spectrum
        spect_analysis = analyze_spectrum(samples, sample_rate=sample_rate, max_peaks=2)

        # [ ] Detect Signal
        det_signal = detect_signal(analysis=spect_analysis, scheme=ModScheme.FSK2)

        # [ ] Downconvert
        if det_signal.center_frequency > 0 or det_signal.center_frequency < 0:
            translated = downconvert_signal(samples=samples, sample_rate=sample_rate,
                                            center_freq=det_signal.center_frequency)
        else:
            translated = samples

        # DEMOD
        # [ ] Demod to Real Symbols
        waveform = demod_to_waveform(samples=translated, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate)  # Reshaped to symbol boundaries
        # [ ] Time Sync w/ Interpolation
        # mm_wave = recover_clock_mm(waveform, sps, interp=None)  # Do not interpolate
        mm_wave = recover_clock_mm(waveform, sps, interp=16)  # Interpolate for better boundaries
        # TO DO: DON'T DO NOW... Get back to the 2nd half of FSK2
        # binary = demod_to_bytes_partial(real_wave=mm_wave, sample_rate=sample_rate,
        #                                 symbol_rate=symbol_rate)
        threshold = numpy.median(mm_wave)
        bits = (mm_wave > threshold).astype(numpy.uint8)
        binary = b''.join(str(bit).encode() for bit in bits)

        # [ ] Frame Sync
        index = correlate_it(binary, DEF_SYNCWORD)
        new_binary = binary[index + len(DEF_SYNCWORD):]

        # [ ] Parse Payload
        parse_payload(new_binary)
    except Exception as err:
        print(f'Execution failed with: {repr(err)}', file=sys.stderr, flush=True)
        raise err from err  # DEBUGGING
# pylint: enable=too-many-locals


if __name__ == '__main__':
    main()
