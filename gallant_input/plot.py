"""Plot graphs."""

# Standard Imports
# Third Party Imports
import matplotlib.pyplot as plt
import numpy
# Local Imports
from gallant_input.signal import compute_spectrum
from gallant_input.validation import validate_int_or_float, validate_ndarray, validate_string


def plot_constellation(samples: numpy.ndarray, title: str | None = 'IQ Constellation') -> None:
    """Plot an IQ constellation (scatter plot of I vs Q).

    Args:
        signal: An array object which represents a complex signal to plot.
        title: [OPTIONAL] The title of the plot.  If empty or None, no title will be added.
    """
    # INPUT VALIDATION
    validate_ndarray(samples, 'samples', must_be_complex=True)
    if title:
        validate_string(title, 'title', can_be_empty=True)

    # PLOT IT
    plt.figure()
    plt.scatter(samples.real, samples.imag, s=1)
    plt.xlabel("In-phase (I)")
    plt.ylabel("Quadrature (Q)")
    if title:
        plt.title(title)
    plt.grid()
    plt.axis('equal')
    plt.show()


def plot_spectrum(signal: numpy.ndarray, samp_rate: int | float,
                     shift_result: bool = True, title: str | None = 'Magnitude Spectrum') -> None:
    """Plot magnitude spectrum of a signal.

    Args:
        signal: The signal to evaluate.
        samp_rate: The sampling frequency in Hz.
        shift_result: [OPTIONAL] If True, rotate both arrays so that 0 Hz is in the center.
    """
    # LOCAL VARIABLES
    freq_map = None  # Frequency mapping of signal
    mag_map = None   # Magnitude mapping of signal

    # INPUT VALIDATION
    if title is not None:
        validate_string(title, 'title')
    freq_map, mag_map = compute_spectrum(signal=signal, samp_rate=samp_rate,
                                         shift_result=shift_result)

    # PLOT IT
    plt.figure()
    plt.plot(freq_map, mag_map)
    plt.xlabel('Frequency (Hz)')
    plt.ylabel('Magnitude')
    if title:
        plt.title(title)
    plt.grid()
    plt.show()


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
    y_plot = None             # The y-axis
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
    plt.plot(x_plot, samples.real, label="I (Real)")
    if numpy.iscomplexobj(samples):
        plt.plot(x_plot, samples.imag, label="Q (Imag)")
    plt.xlabel(x_label)
    plt.ylabel(y_label)
    if title:
        plt.title(title)
    plt.legend()
    plt.grid()
    plt.show()
