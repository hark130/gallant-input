"""Manipulate signals."""

# Standard Imports
import math
# Third Party Imports
from numpy.typing import ArrayLike
from scipy.fft import fft, fftfreq
from scipy.signal import firwin
import numpy
# Local Imports
from gallant_input.validation import (validate_arraylike, validate_float, validate_int,
                                      validate_string, validate_pos_float, validate_pos_int,
                                      validate_type)


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
    return _call_fft(signal=signal)


def compute_frequency_axis(num_samp: int, samp_rate: int | float) -> numpy.ndarray:
    """Return the Discrete Fourier Transform sample frequency bin centers.

    Generate the frequency bin centers in cycles per unit of the sample spacing (1/samp_rate)
    (with zero at the start) for use in plotting.

    Args:
        num_samp: Number of samples.
        samp_rate: The sampling frequency in Hz.

    Returns:
        Array of frequency values in Hz.
    """
    return _call_fftfreq(win_len=num_samp, spacing=1/samp_rate)


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
    validate_type(var=signal, var_name='signal', var_type=numpy.ndarray)
    if axis_len is not None:
        validate_int(axis_len, 'axis_len')
    validate_int(axis, 'axis')
    if norm is not None:
        validate_string(norm, 'norm', can_be_empty=False)
    validate_type(overwrite, 'overwrite', bool)
    if workers is not None:
        validate_int(workers, 'workers')


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
    # int?
    try:
        validate_int(spacing, 'spacing')
    except TypeError:
        pass  # Ignoring one failure
    else:
        num_scalar = True
    # float?
    if not num_scalar:
        try:
            validate_float(spacing, 'spacing')
        except TypeError:
            pass  # Ignoring one failure
        else:
            num_scalar = True
    # complex?
    if not num_scalar:
        try:
            validate_type(spacing, 'spacing', complex)  # Last chance
        except TypeError:
            raise TypeError('The "spacing" argument must be a numerical scalar instead of '
                            f'type {type(spacing)}')
