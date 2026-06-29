"""Manipulate signals."""

# Standard Imports
from typing import Tuple
# Third Party Imports
from numpy.fft import fftshift
from scipy.fft import fft, fftfreq
import numpy
# Local Imports
from gallant_input.detectedsignal import DetectedSignal
from gallant_input.modscheme import ModScheme
from gallant_input.oversamplefactor import OversampleFactor
from gallant_input.spectrumanalysis import SpectrumAnalysis
from gallant_input.validation import (validate_bool, validate_int, validate_pos_float_or_int,
                                      validate_int_or_float, validate_ndarray, validate_pos_int,
                                      validate_string, validate_type)


def compute_basic_fft(signal: numpy.ndarray) -> numpy.ndarray:
    """Compute the 1-D discrete FFT of a signal, with good default values, using scipy.fft.fft().

    Convert a time-domain signal into its complex frequency-domain representation using the
    Fast Fourier Transform (FFT).

    Args:
        signal: An array object which represents a signal to transform.  Can be real or complex.

    Returns:
        The truncated or zero-padded input transformed along the last axis.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return compute_fft(signal=signal)


# It's not my fault.  It's NumPy!
# pylint: disable=too-many-arguments,too-many-positional-arguments
def compute_fft(signal: numpy.ndarray, axis_len: int | None = None, axis: int = -1,
                norm: str | None = None, overwrite: bool = False,
                workers: int | None = None) -> numpy.ndarray:
    """Compute the 1-D discrete FFT of a signal using scipy.fft.fft().

    Convert a time-domain signal into its complex frequency-domain representation using the
    Fast Fourier Transform (FFT).  This docstring has been paraphrased/derived/interpreted from
    https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.fft.fft.html.

    Args:
        signal: An array object which represents a signal to transform.  Can be real or complex.
        axis_len: [OPTIONAL] (AKA 'n' in help(scipy.fft.fft))
        axis: [OPTIONAL] Axis over which to compute the FFT.  If not given, the last axis is used.
        norm: [OPTIONAL] {'backward', 'ortho', 'forward'}
            Normalization mode. Default is 'backward', meaning no normalization on the forward
            transforms and scaling by 1/n on the ifft. 'forward' instead applies the 1/n factor
            on the forward transform. For norm='ortho', both directions are scaled by 1/sqrt(n).
        overwrite: [OPTIONAL] If True, the contents of signal can be destroyed.
        workers: [OPTIONAL] Maximum number of workers to use for parallel computation.
            If negative, the value wraps around from os.cpu_count().

    Returns:
        The truncated or zero-padded input transformed along the last axis.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return _call_fft(signal=signal, axis_len=axis_len, axis=axis, norm=norm,
                     overwrite=overwrite, workers=workers)
# pylint: enable=too-many-arguments,too-many-positional-arguments


def compute_frequency_axis(num_samp: int, samp_rate: int | float | None) -> numpy.ndarray:
    """Return the Discrete Fourier Transform sample frequency bin centers.

    Generate the frequency bin centers in cycles per unit of the sample spacing (1/samp_rate)
    (with zero at the start) for use in plotting.

    Args:
        num_samp: Number of samples.
        samp_rate: [OPTIONAL] The sampling frequency in Hz.  If None, fftfreq() will use a
            default value.

    Returns:
        Array of frequency values in Hz.
    """
    dynamic_kwargs = {'win_len': num_samp}  # Dynamic keyword arguments
    if samp_rate is not None:
        dynamic_kwargs['spacing'] = 1/samp_rate
    return _call_fftfreq(**dynamic_kwargs)


def compute_magnitude_spectrum(signal: numpy.ndarray) -> numpy.ndarray:
    """Calculate the absolute value of each element in signal.

    Args:
        signal: An array object which represents a signal to transform.  Can be real or complex.

    Returns:
        An ndarray containing the absolute value of each element in signal.  For complex input,
        a + ib, the absolute value is sqrt{ a^2 + b^2 }.
    """
    validate_ndarray(array=signal, array_name='signal')
    return numpy.absolute(signal)


def compute_spectrum(signal: numpy.ndarray, samp_rate: int | float | None = None,
                     axis_len: int | None = None, shift_result: bool = True,
                     convert_db: bool = True) -> Tuple[numpy.ndarray, numpy.ndarray]:
    """Calculate the frequencies of the FFT bins, from signal, and the strength of each.

    1. Calculate FFT bins
    2. Map FFT bins to frequencies
    3. Computer the strength of each frequency

    Args:
        signal: The signal to evaluate.
        samp_rate: [Optional] The sampling frequency in Hz.  If None, library defaults will be used.
        axis_len: [OPTIONAL] See: help(compute_fft) (AKA 'n' in help(scipy.fft.fft)).
        shift_result: [OPTIONAL] If True, rotate both arrays so that 0 Hz is in the center.
        convert_db: [OPTIONAL] Convert y-axis values to decibels.

    Returns:
        A tuple containing the mapped frequencies (x-axis?) and the magnitude of each (y-axis?).

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    fft_arr = None       # Compute the 1-D discrete FFT of a signal
    freq_map = None      # The Discrete Fourier Transform sample frequency bin centers
    mag_map = None       # The absolute value of each element in signal
    num_samp = axis_len  # Window length to compute the Discrete Fourier Transform sample freqs

    # INPUT VALIDATION
    validate_bool(shift_result, 'shift_result')
    validate_bool(convert_db, 'convert_db')
    _validate_axis_len(axis_len=axis_len)

    # COMPUTE IT
    # 1. Calculate FFT bins
    fft_arr = compute_fft(signal=signal, axis_len=axis_len)
    # 2. Map FFT bins to frequencies
    if num_samp is None:
        num_samp = len(fft_arr)
    freq_map = compute_frequency_axis(num_samp=num_samp, samp_rate=samp_rate)
    # 3. Compute the strength of each frequency
    mag_map = compute_magnitude_spectrum(signal=fft_arr)

    # SHIFT IT
    if shift_result:
        freq_map = fftshift(freq_map)
        mag_map = fftshift(mag_map)
    if convert_db:
        mag_map = convert_mag_to_db(mag_map)

    # DONE
    return tuple((freq_map, mag_map))


def convert_mag_to_db(mag_map: numpy.ndarray) -> numpy.ndarray:
    """Convert a magnitude mapping to decibels.

    Args:
        mag_map: An array of absolute magnitudes to convert to decibels.

    Returns:
        An ndarray of mag_map values converted to decibels.
    """
    # LOCAL VARIABLES
    db_map = None  # The mag_map arg converted to decibels

    # INPUT VALIDATION
    validate_ndarray(mag_map, 'mag_map', can_be_empty=False)

    # CONVERT IT
    db_map = 20 * numpy.log10(mag_map + 1e-12)

    # DONE
    return db_map


def detect_signal(analysis: SpectrumAnalysis, scheme: ModScheme) -> DetectedSignal:
    """Select a signal of interest from a spectral analysis based on a modulation scheme.

    Examines the peaks detected within a spectrum and identifies a candidate signal for reception.
    Depending on the detection strategy, a signal may consist of one or more spectral peaks.

    Examples include:
        * OOK: one dominant peak
        * BFSK: two dominant peaks
        * BPSK: one broad lobe
        * OFDM: many subcarriers

    This function performs signal selection only. It does not modify the input samples.

    Args:
        analysis: Spectrum analysis (Call analyze_spectrum() first).

    Returns:
        A DetectedSignal describing the selected transmission.

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    signal = None  # DetectedSignal obj

    # INPUT VALIDATION
    validate_type(analysis, 'analysis', SpectrumAnalysis)
    validate_type(scheme, 'scheme', ModScheme)

    # DETECT IT
    match scheme:
        case scheme.FSK2:
            signal = _detect_signal_num_peaks(analysis=analysis, num_peaks=2)
        case _:
            raise UnimplementedError(f'This modulation scheme is not yet supported: {scheme}')

    # DONE
    return signal


def downconvert_signal(samples: numpy.ndarray, sample_rate: float | int,
                       center_freq: float | int) -> numpy.ndarray:
    """Frequency translate a sampled signal to complex baseband.

    Multiplies the input samples by a complex exponential whose frequency matches the supplied
    center frequency. The effect is to shift the selected signal to 0 Hz while preserving its
    complex envelope.

    Args:
        samples: Complex-valued input samples.
        sample_rate: Sampling rate of the input samples in Hz.
        center_freq: Frequency offset to remove, in hertz.

    Returns:
        Frequency-translated complex samples.

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    time_arr = None    # 0-N time array
    osc = None         # Oscillator array
    translated = None  # Downconverted signal

    # INPUT VALIDATION
    validate_ndarray(samples, 'samples', can_be_empty=False, num_dim=1, must_be_complex=True)
    validate_pos_float_or_int(sample_rate, 'sample_rate')
    validate_int_or_float(center_freq, 'center_freq')

    # DOWNCONVERT IT
    time_arr = numpy.arange(len(samples))
    # Negate the oscillator (because multiplication adds frequencies)
    osc = numpy.exp(-1j * 2 * numpy.pi * center_freq * time_arr / sample_rate)
    translated = samples * osc

    # DONE
    return translated


def optimize_window_size(coeffs: numpy.ndarray,
                         oversample: OversampleFactor = OversampleFactor.DEFAULT,
                         min_size: int = 1024) -> int:
    """Apply an algorithm to determine an optimal window size: smooth, yet fast.

    Use this function to optimally pad the window sized, based on the number of coefficients,
    so that the impulse response is padded with zeros before computing the frequency response.

    Args:
        coeffs: A 1-dimensional array of filter coefficients (AKA impulse response).
        oversample: [OPTIONAL] An oversampling factor in the frequency domain (K).
        min_size: [OPTIONAL] Ensures a minimum FFT window size.  If overriding the default value,
            ensure the value is a power of 2.

    Returns:
        An optimal window size based on the oversampling value and the size of coeffs.
    """
    # LOCAL VARIABLES
    next_pow = min_size  # Next power of 2

    # INPUT VALIDATION
    validate_ndarray(coeffs, 'coeffs', can_be_empty=False, num_dim=1, must_be_complex=False)
    validate_type(oversample, 'oversample', OversampleFactor)
    _validate_power_of_two(min_size, 'min_size')

    # OPTIMIZE IT
    next_pow = 1 << (int(len(coeffs) * oversample) - 1).bit_length()

    # DONE
    return max(min_size, next_pow)


# It's not my fault.  It's NumPy!
# pylint: disable=too-many-arguments,too-many-positional-arguments
def _call_fft(signal: numpy.ndarray, axis_len: int | None = None, axis: int = -1,
              norm: str | None = None, overwrite: bool = False,
              workers: int | None = None) -> numpy.ndarray:
    """A SPOT to call scipy.fft.fft().

    This function standardizes how this module validates the input to scipy.fft.fft()
    and calls it.

    Note:
        - The scipy.fft.fft(plan) argument, reserved for passing in a precomputed plan provided by
          downstream FFT vendors, is being ignored here because it is currently not used in SciPy.

    See help(compute_fft), help(scipy.fft.fft), or
    https://docs.scipy.org/doc/scipy-1.16.1/reference/generated/scipy.fft.fft.html#fft
    for more details on the arguments.

    Returns:
        The truncated or zero-padded input, transformed along the axis indicated by `axis`,
        or the last one if `axis` is not specified.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    _validate_fft_args(signal=signal, axis_len=axis_len, axis=axis, norm=norm,
                       overwrite=overwrite, workers=overwrite)
    return fft(signal, n=axis_len, axis=axis, norm=norm, overwrite_x=overwrite, workers=workers)
# pylint: enable=too-many-arguments,too-many-positional-arguments


def _call_fftfreq(win_len: int, spacing: int | float | complex = 1.0) -> numpy.ndarray:
    """

    Note:
        - The scipy.fft.fftfreq(xp) argument, used to indicate different namespaces for the
          return array instead of NumPy, is being ignored here because NumPy is good enough.
        - The scipy.fft.fftfreq(device) argument, used to specify the device for the return array,
          is being ignored here because the CPU is good enough.

    Args:
        win_len: Window length.
        samp_period: [OPTIONAL] Sample spacing (inverse of the sampling rate). Defaults to 1.

    Returns:
        An array of length win_len containing the sample frequencies.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    _validate_fftfreq_args(win_len=win_len, spacing=spacing)
    return fftfreq(n=win_len, d=spacing)


def _detect_signal_num_peaks(analysis: SpectrumAnalysis, num_peaks: int) -> DetectedSignal:
    """Detect a given number of peaks."""
    # LOCAL VARIABLES
    act_peaks = len(analysis.peaks)  # The number of peaks in analysis
    peak_list = []                   # The top peaks from analysis
    center_frequency = 0             # Center frequency of the peaks
    bandwidth = 0                    # Total bandwidth of the peaks
    left = 0                         # Leftmost frequency
    right = 0                        # Rightmost frequency

    # INPUT VALIDATION
    validate_pos_int(num_peaks, 'num_peaks')
    if act_peaks < num_peaks:
        raise ValueError(f'The "analysis" parameter only contains {act_peaks} which is not '
                         f'enough to match {num_peaks}')

    # DETECT IT
    peak_list = analysis.peaks[:num_peaks]
    # Center Frequency
    for peak_entry in peak_list:
        center_frequency += peak_entry.frequency
    center_frequency = center_frequency / len(peak_list)
    # Total Bandwidth
    left = min(peak_entry.left_edge for peak_entry in peak_list)
    right = max(peak_entry.right_edge for peak_entry in peak_list)
    bandwidth = right - left
    center_frequency = (left + right) / 2

    # DONE
    return DetectedSignal(center_frequency=center_frequency, bandwidth=bandwidth, peaks=peak_list)


def _validate_axis_len(axis_len: int | None = None) -> None:
    """Validate a common keyword argument on behalf of this module."""
    if axis_len is not None:
        validate_int(axis_len, 'axis_len')


# It's not my fault.  It's NumPy!
# pylint: disable=too-many-arguments,too-many-positional-arguments
def _validate_fft_args(signal: numpy.ndarray, axis_len: int | None = None, axis: int = -1,
                       norm: str | None = None, overwrite: bool = False,
                       workers: int | None = None) -> None:
    """Validate scipy.fft.fft() arguments on behalf of the module.

    Args:
        See help(_call_fft) for a description of the arguments.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # ARGUMENT VALIDATION
    validate_ndarray(signal, 'signal')
    _validate_axis_len(axis_len=axis_len)
    validate_int(axis, 'axis')
    if norm is not None:
        validate_string(norm, 'norm', can_be_empty=False)
    validate_bool(overwrite, 'overwrite')
    if workers is not None:
        validate_int(workers, 'workers')
# pylint: enable=too-many-arguments,too-many-positional-arguments


def _validate_fftfreq_args(win_len: int, spacing: int | float | complex = 1.0) -> None:
    """Validate scipy.fft.fftfreq() arguments on behalf of the module.

    Args:
        See help(_call_fftfreq) for a description of the arguments.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    validate_pos_int(win_len, 'win_len')
    _validate_fftfreq_scalar(spacing=spacing)


def _validate_fftfreq_scalar(spacing: int | float | complex) -> None:
    """Validate a scipy.fft.fftfreq(d) numerical scalar on behalf of this module.

    The documentation for scipy.fft.fftfreq()'s "d" argument claims it takes a scalar but it
    doesn't accept *all* scalars.  In observation, it only accepts numerical scalars.
    """
    # LOCAL VARIABLES
    num_scalar = False  # Flow control variable

    # VALIDATE IT
    # int or float?
    try:
        validate_int_or_float(spacing, 'spacing')
    except TypeError:
        pass  # Ignoring one failure
    else:
        num_scalar = True
    # complex?
    if not num_scalar:
        try:
            validate_type(spacing, 'spacing', complex)  # Last chance
        except TypeError:
            # I don't want to "raise from" because this exception is shared by two try/excepts
            # pylint: disable=raise-missing-from
            raise TypeError('The "spacing" argument must be a numerical scalar instead of '
                            f'type {type(spacing)}')
            # pylint: enable=raise-missing-from


def _validate_power_of_two(validate_this: int, param_name: str) -> None:
    """Validate that a value is a power of 2."""
    validate_pos_int(validate_this, param_name)
    if (validate_this & (validate_this - 1)) != 0:
        raise ValueError(f'The value of "{validate_this}" is not a power of two')
