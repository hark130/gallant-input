"""Born from my shmelstone_receiver and refactored to escape CPT Fox Time (CFT).

Example Usage:
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_hark1.sigmf-data
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_msg1_max.sigmf-data
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_msg2_long.sigmf-data
    python -m rxtx.static_rx_shmelstone ./data/shmelstone_filt_cap_c912m_s2p4m_msg3_med.sigmf-data
"""

# Standard Imports
from pathlib import Path
from scipy import signal
from typing import Any, Final
import numpy  # CFT
import sys
# Third Party Imports
import matplotlib.pyplot as plt
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.codec import convert_ascii_bin_bytes_to_bits, upsample
from gallant_input.constants import SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT
from gallant_input.converters import (convert_bin_bytes_to_ascii, convert_bin_bytes_to_int,
                                      convert_bin_bytes_to_ndarray)
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modscheme import ModScheme
from gallant_input.plot import (plot_constellation, plot_time_domain, plot_spectrum,
                                plot_symbol_boundaries)
from gallant_input.signal import (compute_basic_fft, decimate_samples, detect_signal,
                                  downconvert_signal, squelch_signal)
from gallant_input.synch.frame import correlate_it
from gallant_input.synch.timing import recover_clock_mm
from gallant_input.timing import estimate_symbol_clock

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
    else:
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
    print(f'User "{user_name}" sent message: {message}')


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
        spect_analysis = None             # SpectrumAnalysis obj
        signal = None                     # DetectedSignal obj
        binary = b''                      # Demodulated binary
        waveform = None                   # Demodulated real waveform
        index = 0                         # Correlated index
        new_binary = b''                  # Frame synch'd binary
        decimate = 20                     # Decimation

        # DO IT
        # Fetch SigMF metadata (if available)
        if filepath.suffix.lower() == f'.{SIGMF_DATA_FILE_EXT}'.lower():
            sig_meta_parser = SigMFMetaParser(filepath.with_suffix(f'.{SIGMF_META_FILE_EXT}'))
            sample_rate = sig_meta_parser.get_sample_rate()
        # Decimate!
        samples = decimate_samples(samples=samples, decimate=decimate)
        sample_rate = sample_rate / decimate
        sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Calc the sps
        # print(f'SPS: {sps}')  # DEBUGGING
        # print(f'SAMPLE RATE: {sample_rate}')  # DEBUGGING
        # Squelch!
        # samples = squelch_signal(signal=samples, threshold=-50)
        # samples = squelch_signal(signal=samples, threshold=-49)
        samples = squelch_signal(signal=samples, threshold=-48)
        # samples = squelch_signal(signal=samples, threshold=-47)
        # samples = squelch_signal(signal=samples, threshold=-45)
        # samples = squelch_signal(signal=samples, threshold=-30)
        # samples = squelch_signal(signal=samples, threshold=-15)
        # Analyze Spectrum
        spect_analysis = analyze_spectrum(samples, sample_rate=sample_rate, max_peaks=2)
        # print(spect_analysis)  # DEBUGGING
        # Detect Signal
        signal = detect_signal(analysis=spect_analysis, scheme=ModScheme.FSK2)
        # print(signal)  # DEBUGGING
        # DOWNCONVERT(?) AND PLOT
        if signal.center_frequency > 0 or signal.center_frequency < 0:
            translated = downconvert_signal(samples=samples, sample_rate=sample_rate,
                                            center_freq=signal.center_frequency)
            # plot_spectrum(translated, samp_rate=sample_rate, title='Downconverted Freq vs. Mag')
        else:
            translated = samples
        #     plot_spectrum(translated, samp_rate=sample_rate, title='Original Freq vs. Mag')
        # est_sps = estimate_symbol_clock(translated, sps)
        # print(f'SPS CALC "{sps}" ESTIMATED "{est_sps}"')  # DEBUGGING
        # sps = est_sps  # DEBUGGING
        waveform = demod_to_waveform(samples=translated, sample_rate=sample_rate,
                                     symbol_rate=symbol_rate)  # Used by 2 & 3
        correlate_this = upsample(convert_ascii_bin_bytes_to_bits(DEF_SYNCWORD), sps)  # Syncword

        # DEMOD
        # Attempt 6 - Time Sync w/ Interpolation

        # Attempt 5 - M&M
        # print(f'WAVEFORM LEN: {len(waveform)}')  # DEBUGGING
        # plot_symbol_boundaries(waveform, sps)
        # timing = recover_symbol_centers(waveform, sps, 0.1)
        # mm_wave = recover_clock_mm(waveform, sps, interp=None)  # Do not interpolate
        mm_wave = recover_clock_mm(waveform, sps, interp=16)  # Interpolate for better boundaries
        # binary = demod_to_bytes_partial(real_wave=mm_wave, sample_rate=sample_rate,
        #                                 symbol_rate=symbol_rate)
        threshold = numpy.median(mm_wave)
        bits = (mm_wave > threshold).astype(numpy.uint8)
        binary = b''.join(str(bit).encode() for bit in bits)

        # Attempt 4 - Timing recover
        # timing = recover_symbol_centers(waveform, sps, 1)
        # print(f'TIMING SYMBOLS: {timing.symbols}')  # DEBUGGING
        # # binary = demod_to_bytes_partial(real_wave=timing.symbols, sample_rate=sample_rate,
        # #                                 symbol_rate=symbol_rate)
        # threshold = numpy.median(timing.symbols)
        # bits = (timing.symbols > threshold).astype(numpy.uint8)
        # # print(f'BITS: {bits}')  # DEBUGGING
        # binary = b''.join(str(bit).encode() for bit in bits)
        # print(f'BINARY: {binary}')
        # parse_payload(binary)
        # # Plot
        # plt.plot(waveform)
        # for c in timing.predicted_centers:
        #     plt.axvline(c, linestyle=":", color='red')
        # for c in timing.centers:
        #     plt.axvline(c, color='purple')
        # plt.show()

        # Attempt 3 - Correlate on the real waveform
        # print(f'SOME PREAMBLE + SYNCWORD (len {len(DEF_PREAMWRD)}): {DEF_PREAMWRD}')  # DEBUGGING
        # sps = est_sps  # DEBUGGING
        # index = correlate_it(waveform, correlate_this)  # Used by 3 & 4
        # # print(f'INDEX: {index} (OF {len(waveform)} SAMPLES)')  # DEBUGGING
        # waveform = waveform[index + len(correlate_this):]  # Index past the preamble
        # waveform = waveform[index + len(correlate_this) + int(sps/3):]  # WINGIN' IT... EE-style
        # # print(f'INDEX: {index} (OF {len(waveform)} SAMPLES)')  # DEBUGGING
        # plot_symbol_boundaries(waveform, sps)
        # binary = demod_to_bytes_partial(real_wave=waveform, sample_rate=sample_rate,
        #                                 symbol_rate=symbol_rate)
        # print(f'BINARY: {binary}')  # DEBUGGING
        # parse_payload(binary)
        # BRUTE FORCE IT
        # wave_copy = None
        # for offset in range(0, index * 2, 1000):
        #     try:
        #         wave_copy = waveform[offset + len(correlate_this):]  # Index past the preamble
        #         binary = demod_to_bytes_partial(real_wave=wave_copy, sample_rate=sample_rate,
        #                                         symbol_rate=symbol_rate)
        #         print(f'BINARY (OFFSET {offset} INDEX {index}): {binary}')  # DEBUGGING
        #         parse_payload(binary)
        #     except Exception as err:
        #         print(f'OFFSET {offset} INDEX {index} RAISED {err}')

        # Attempt 1 - Frame Sync
        # binary = demod_to_bytes_full(samples=translated, sample_rate=sample_rate,
        #                              symbol_rate=symbol_rate)
        # print(f'BINARY: {binary}')  # DEBUGGING
        index = correlate_it(binary, DEF_SYNCWORD)
        # print(f'INDEX: {index}')  # DEBUGGING
        new_binary = binary[index + len(DEF_SYNCWORD):]
        # print(f'FRAME SYNC BINARY: {new_binary}')  # DEBUGGING
        parse_payload(new_binary)

        # Attempt 2 - Waveform Sync
        # plot_symbol_boundaries(waveform, sps)
        # plot_time_domain(samples=waveform, samp_rate=sample_rate, title='Demod Real Waveform')
    except Exception as err:
        print(f'Execution failed with: {repr(err)}', file=sys.stderr, flush=True)
        raise err from err  # DEBUGGING


if __name__ == '__main__':
    main()
