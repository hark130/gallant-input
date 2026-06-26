"""Born from my shmelstone_receiver and refactored to escape CPT Fox Time (CFT)."""

# Standard Imports
from pathlib import Path
import numpy  # CFT
import sys
# Third Party Imports
# Local Imports
from gallant_input.analyze import analyze_spectrum
from gallant_input.codec import upsample
from gallant_input.converters import convert_bin_bytes_to_ascii, convert_bin_bytes_to_int
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_sps
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from gallant_input.modscheme import ModScheme
from gallant_input.plot import plot_constellation, plot_time_domain, plot_spectrum
from gallant_input.signal import compute_basic_fft, detect_signal

DEF_SAMP_RATE: Final[int] = 2400000


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


def main() -> None:
    """do_it()."""
    try:
        filepath = get_filename()
        samples = read_samples(filepath)    
        spect_analysis = analyze_spectrum(samples, sample_rate=DEF_SAMP_RATE, max_peaks=2)
        print(spect_analysis)
        signal = detect_signal(analysis=spect_analysis, scheme=ModScheme.FSK2)
        print(signal)
        # plot_constellation(samples)
        plot_spectrum(samples, samp_rate=DEF_SAMP_RATE)
    except Exception as err:
        print(f'Execution failed with: {repr(err)}', file=sys.stderr, flush=True)
        # raise err from err


if __name__ == '__main__':
    main()
