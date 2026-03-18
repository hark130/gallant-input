"""Plot graphs."""

# Standard Imports
# Third Party Imports
import matplotlib.pyplot as plt
import numpy
# Local Imports
from gallant_input.signal import compute_spectrum
from gallant_input.validation import (validate_int_or_float, validate_ndarray, validate_pos_float,
                                      validate_string)


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


# Maybe I'll refactor this later...
# pylint: disable=too-many-arguments,too-many-positional-arguments
def plot_spectrum(signal: numpy.ndarray, samp_rate: int | float,
                  shift_result: bool = True, convert_db: bool = True,
                  center_freq: float | None = None,
                  title: str | None = 'Magnitude Spectrum') -> None:
    """Plot magnitude spectrum of a signal.

    Args:
        signal: The signal to evaluate.
        samp_rate: The sampling frequency in Hz.
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
    plt.figure()
    plt.plot(freq_map, mag_map, label='FFT')
    _plot_it(x_label=x_label, y_label=y_label, title=title)
# pylint: enable=too-many-arguments,too-many-positional-arguments


def plot_time_domain(samples: numpy.ndarray, samp_rate: int | float | None = None,
                     title: str | None = 'Time Domain') -> None:
    """Plot real and imaginary components of a signal over time.

    Args:
        signal: An array object which represents a signal to plot.  Can be real or complex.
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
             title: str | None = None) -> None:
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

    # PLOT IT
    plt.legend()
    plt.grid()
    plt.show()
