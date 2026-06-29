"""Born from my shmelstone_receiver and refactored to escape CPT Fox Time (CFT).

Example Usage:
    python static_receiver.py ./data/shmelstone_filt_cap_c912m_s2p4m_msg3_not_short.sigmf-data
"""

# Standard Imports
from pathlib import Path
from typing import Any, Final
import numpy  # CFT
import sys
# Third Party Imports
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.codec import upsample
from gallant_input.constants import SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT
from gallant_input.converters import convert_bin_bytes_to_ascii, convert_bin_bytes_to_int
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modscheme import ModScheme
from gallant_input.plot import plot_constellation, plot_time_domain, plot_spectrum
from gallant_input.signal import compute_basic_fft, detect_signal, downconvert_signal

DEF_SAMP_RATE: Final[int] = 2400000
DEF_SYMB_RATE: Final[int] = 2400
DEF_SYNCWORD: Final[bytes] = b'11010011100100011101001110010001'  # 0xD391 0xD391


def convert_bin_bytes_to_ndarray(bin_bytes: bytes, bipolar: bool = True) -> numpy.ndarray:
    """Convert binary bytes to an ndarray."""
    bits = (numpy.frombuffer(bin_bytes, dtype=numpy.uint8) == ord('1')).astype(numpy.int8)

    if bipolar is True:
        return bits * 2 - 1

    return bits


def correlate_it(thing1: Any, thing2: Any) -> int:
    """Correlate thing2 with thing1 returning a thing1 index of highest correlation."""
    # LOCAL VARIABLES
    arr1 = thing1
    arr2 = thing2
    corr = None    # Correlation array
    index = 0      # Index of highest correlation into thing1 (AKA arr1)

    # SETUP
    if isinstance(arr1, bytes):
        arr1 = convert_bin_bytes_to_ndarray(arr1)
    if isinstance(arr2, bytes):
        arr2 = convert_bin_bytes_to_ndarray(arr2)

    # CORRELATE IT
    corr = numpy.correlate(arr1, arr2, mode='valid')
    index = int(corr.argmax())

    # DONE
    return index


def demod_to_bytes(samples: numpy.ndarray, sample_rate: float | int,
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


def squelch_it(samples: numpy.ndarray, threshold: float | int) -> numpy.ndarray:
    """Squelch the samples given a threshold."""
    mag = numpy.abs(samples)        # Magnitude
    mag_db = 10 * numpy.log10(mag)  # Convert magnitude to power
    squelched = samples[mag_db > threshold]
    return squelched


def main() -> None:
    """do_it()."""
    try:
        # LOCAL VARIABLES
        sig_meta_parser = None            # The SigMFMetaParser (if filepath is a SigMF file)
        sample_rate = DEF_SAMP_RATE       # Capture sample rate
        symbol_rate = DEF_SYMB_RATE       # Capture symbol rate
        filepath = get_filename()         # CLI capture file
        samples = read_samples(filepath)  # Samples read from the capture
        translated = samples              # Downshifted samples to 0 Hz center frequency
        spect_analysis = None             # SpectrumAnalysis obj
        signal = None                     # DetectedSignal obj
        binary = b''                      # Demodulated binary
        index = 0                         # Correlated index
        new_binary = b''                  # Frame synch'd binary

        # DO IT
        # Fetch SigMF metadata (if available)
        if filepath.suffix.lower() == f'.{SIGMF_DATA_FILE_EXT}'.lower():
            sig_meta_parser = SigMFMetaParser(filepath.with_suffix(f'.{SIGMF_META_FILE_EXT}'))
            sample_rate = sig_meta_parser.get_sample_rate()
        # Squelch!
        samples = squelch_it(samples=samples, threshold=-30)
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
        # DEMOD
        binary = demod_to_bytes(samples=translated, sample_rate=sample_rate,
                                symbol_rate=symbol_rate)
        print(f'BINARY: {binary}')  # DEBUGGING
        index = correlate_it(binary, DEF_SYNCWORD)
        new_binary = binary[index + len(DEF_SYNCWORD):]
        print(f'FRAME SYNC BINARY: {new_binary}')  # DEBUGGING
        print(f'DECODED (INDEX {index}): {convert_bin_bytes_to_ascii(new_binary)}')
        # TO DO: DON'T DO NOW...
        #   - Write a decode_payload() function (replicating CFT)
        #   - Verify the integrity of the capture by manually decoding the message: Inspectrum, URH
        #   - Comment out/remove the janky timing attempt inside FSK2
        #   - Consider rolling back to the original FSK2.demod() attempt
        #   - Try to correlate on the real demod samples instead of the binary
        #   - Try the half-over coarse timing sync (on the real demod samples)
    except Exception as err:
        print(f'Execution failed with: {repr(err)}', file=sys.stderr, flush=True)
        raise err from err  # DEBUGGING


if __name__ == '__main__':
    main()
