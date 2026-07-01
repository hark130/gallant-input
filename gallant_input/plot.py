"""Plot graphs."""

# Standard Imports
# Third Party Imports
import matplotlib.pyplot as plt
import numpy
# Local Imports
from gallant_input.signal import compute_spectrum
from gallant_input.validation import (validate_bool, validate_int_or_float, validate_ndarray,
                                      validate_pos_float, validate_pos_int, validate_string)


def plot_constellation(samples: numpy.ndarray, title: str | None = 'IQ Constellation') -> None:
    """Plot an IQ constellation (scatter plot of I vs Q).

    Args:
        signal: An array object which represents a complex signal to plot.
        title: [OPTIONAL] The title of the plot.  If empty or None, no title will be added.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # INPUT VALIDATION
    validate_ndarray(samples, 'samples', must_be_complex=True)

    # PLOT IT
    plt.figure()
    plt.scatter(samples.real, samples.imag, s=1, label='Samples')
    plt.axis('equal')
    _plot_it(x_label='In-phase (I)', y_label='Quadrature (Q)', title=title)


def plot_frequency_response(coeffs: numpy.ndarray, win_size: int | None = None,
                            title: str | None = 'Frequency Response') -> None:
    """Plot the frequency response of filter coefficients.

    Args:
        coeffs: A 1-dimensional array of filter coefficients (AKA impulse response).
        win_size: [OPTIONAL] FFT window size.  Consider using signal.optimize_window_size().
    """
    # LOCAL VARIABLES
    freq_map = None                                   # Frequency mapping of signal
    mag_map = None                                    # Magnitude mapping of signal
    x_label = 'Normalized Frequency (cycles/sample)'  # The x-axis label
    y_label = 'Magnitude (dB)'                        # The y-axis label

    # INPUT VALIDATION
    validate_ndarray(coeffs, 'coeffs', can_be_empty=False, num_dim=1, must_be_complex=False)
    if win_size is not None:
        validate_pos_int(win_size, 'win_size')

    # PLOT IT
    # 1. Compute it
    freq_map, mag_map = compute_spectrum(signal=coeffs, samp_rate=None, axis_len=win_size,
                                         shift_result=True, convert_db=True)
    # 2. Plot it
    _plot_spectrum(freq_map=freq_map, mag_map=mag_map,
                   x_label=x_label, y_label=y_label, title=title)


def plot_impulse_response(coeffs: numpy.ndarray) -> None:
    """Plot filter coefficients.

    Args:
        coeffs: A 1-dimensional array of filter coefficients (AKA impulse response).
    """
    # LOCAL VARIABLES
    x_values = None    # Evenly spaced x-axis values derived from coeffs
    markerline = None  # StemContainer marker line
    stemlines = None   # StemContainer stem line
    baseline = None    # StemContainer base line

    # INPUT VALIDATION
    validate_ndarray(coeffs, 'coeffs', can_be_empty=False, num_dim=1, must_be_complex=False)

    # SETUP
    x_values = numpy.arange(len(coeffs))  # Plot h[n] vs n

    # PLOT IT
    plt.figure()  # Consider figsize=(8, 4)
    # Draw lines perpendicular to a baseline at each location, with markers
    markerline, stemlines, baseline = plt.stem(x_values, coeffs)
    # Style tweaks for textbook look
    plt.setp(markerline, marker='o', markersize=6)  # Makes the dots more visible
    plt.setp(stemlines, linewidth=1.5)  # Clean vertical-line look
    plt.setp(baseline, linewidth=1)  # Emphasizes pos/neg symmetry and visualizes filter shape
    plt.axhline(0, linewidth=1)  # Horizontal axis at zero
    plt.xlim(-1, len(coeffs))  # Tight axis control
    _plot_it(x_label='Index (n)', y_label='h[n]', title='Impulse Response h[n]', visible_grid=False)


# Maybe I'll refactor this later...
# pylint: disable=too-many-arguments,too-many-positional-arguments
def plot_spectrum(signal: numpy.ndarray, samp_rate: int | float | None = None,
                  shift_result: bool = True, convert_db: bool = True,
                  center_freq: float | None = None,
                  title: str | None = 'Magnitude Spectrum') -> None:
    """Plot magnitude spectrum of a signal.

    Plot frequency vs. magnitude.

    Args:
        signal: The signal to evaluate.
        samp_rate: [OPTIONAL] The sampling frequency in Hz.  If None, the library will use defaults.
        shift_result: [OPTIONAL] If True, rotate both arrays so that 0 Hz is in the center.
        convert_db: [OPTIONAL] Convert y-axis values to decibels.
        center_freq: [OPTIONAL] Specify a center frequency on the plot.
        title: [OPTIONAL] The title of the plot.  If empty or None, no title will be added.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    freq_map = None                  # Frequency mapping of signal
    mag_map = None                   # Magnitude mapping of signal
    x_label = 'Frequency (Hz, abs)'  # The x-axis label
    y_label = 'Magnitude'            # The y-axis label

    # INPUT VALIDATION
    if center_freq is not None:
        validate_pos_float(center_freq, 'center_freq')
        x_label = 'Frequency (Hz)'
    freq_map, mag_map = compute_spectrum(signal=signal, samp_rate=samp_rate,
                                         shift_result=shift_result, convert_db=convert_db)
    if center_freq is not None:
        freq_map = freq_map + center_freq
    if convert_db:
        y_label = y_label + ' (dB)'

    # PLOT IT
    _plot_spectrum(freq_map=freq_map, mag_map=mag_map,
                   x_label=x_label, y_label=y_label, title=title)
# pylint: enable=too-many-arguments,too-many-positional-arguments


def plot_symbol_boundaries(real_wave: numpy.ndarray, sps: float | int) -> None:
    """Plot symbol boundaries against a real (demodulated) waveform.

    Args:
        real_wave: The real waveform.
        sps: Samples per symbol.
    """
    # LOCAL VARIABLES
    num_samps = None             # The length of real_wave
    x_label = 'Sample Index'     # The x-axis label
    y_label = 'Inst. Freq'       # The y-axis label
    title = 'Symbol Boundaries'  # The title

    # INPUT VALIDATION
    validate_ndarray(real_wave, 'samples', can_be_empty=False, num_dim=1)
    validate_int_or_float(sps, 'sps')

    # PREPARE
    num_samps = len(real_wave)
    sample_points = numpy.arange(0, num_samps, sps)
    plt.plot(real_wave)
    for sample_point in sample_points:
        plt.axvline(sample_point, color='red', alpha=0.2)

    # PLOT IT
    _plot_it(x_label=x_label, y_label=y_label, title=title)


def plot_time_domain(samples: numpy.ndarray, samp_rate: int | float | None = None,
                     title: str | None = 'Time Domain') -> None:
    """Plot real and imaginary components of a signal over time.

    Args:
        samples: An array object which represents a signal to plot.  Can be real or complex.
        samp_rate: [OPTIONAL] The sampling frequency in Hz.  If None, uses the "samples" indices.
        title: [OPTIONAL] The title of the plot.  If empty or None, no title will be added.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    num_samps = None          # The length of samples
    x_plot = None             # The x-axis
    x_label = 'Sample Index'  # The x-axis label
    y_label = 'Amplitude'     # The y-axis label

    # INPUT VALIDATION
    validate_ndarray(samples, 'samples', can_be_empty=False, num_dim=None)
    if samp_rate is not None:
        validate_int_or_float(samp_rate, 'samp_rate')
    if title:
        validate_string(title, 'title', can_be_empty=True)

    # PREPARE
    num_samps = len(samples)
    if samp_rate is not None:
        x_plot = numpy.arange(num_samps) / samp_rate
        x_label = 'Time (seconds)'
    else:
        x_plot = numpy.arange(num_samps)

    # PLOT IT
    plt.figure()
    plt.plot(x_plot, samples.real, label='I (Real)')
    if numpy.iscomplexobj(samples):
        plt.plot(x_plot, samples.imag, label='Q (Imag)')
    _plot_it(x_label=x_label, y_label=y_label, title=title)


def _plot_it(x_label: str | None = None, y_label: str | None = None,
             title: str | None = None, visible_grid: bool = True) -> None:
    """Create a modular SPOT for this module to display all 'open figrues'.

    Calls:
        plt.xlabel(x_label)
        plt.ylabel(y_label)
        plt.title(title)
        plt.legend()
        plt.grid()
        plt.show()

    Args:
        x_label: [OPTIONAL] Set the label for the x-axis, if defined.
        y_label: [OPTIONAL] Set the label for the y-axis, if defined.
        title: [OPTIONAL] Set the text to use for the title, if defined.
        visible_grid: [OPTIONAL] If True, show the grid lines.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # INPUT VALIDATION
    if x_label is not None:
        validate_string(x_label, 'x_label', can_be_empty=False)
        plt.xlabel(x_label)
    if y_label is not None:
        validate_string(y_label, 'y_label', can_be_empty=False)
        plt.ylabel(y_label)
    if title is not None:
        validate_string(title, 'title', can_be_empty=False)
        plt.title(title)
    validate_bool(visible_grid, 'visible_grid')

    # PLOT IT
    plt.legend()
    plt.grid(visible=visible_grid)
    plt.show()


def _plot_spectrum(freq_map: numpy.ndarray, mag_map: numpy.ndarray, x_label: str | None = None,
                   y_label: str | None = None, title: str | None = None) -> None:
    """Share common functionality between plot_spectrum() and plot_frequency_response().

    Args:
        freq_map: Frequency mapping in a 1-dimensional array.
        mag_map: Magnitude mapping in a 1-dimensional array.
        x_label: [OPTIONAL] Set the label for the x-axis, if defined.
        y_label: [OPTIONAL] Set the label for the y-axis, if defined.
    """
    # PLOT IT
    plt.figure()
    plt.plot(freq_map, mag_map, label='FFT')
    _plot_it(x_label=x_label, y_label=y_label, title=title)
