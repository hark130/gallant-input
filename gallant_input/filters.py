"""Implement FIR/IIR filters."""

# Standard Imports
import math
# Third Party Imports
from numpy.typing import ArrayLike
from scipy.signal import firwin
import numpy
# Local Imports
from gallant_input.constants import FIRWIN_HPF, FIRWIN_LPF
from gallant_input.convolvemode import ConvolveMode
from gallant_input.validation import (validate_arraylike, validate_bool, validate_float,
                                      validate_ndarray, validate_pos_float, validate_pos_int,
                                      validate_string, validate_type)

# I didn't do it this time.  It was firwin()!
# pylint: disable=too-many-arguments, too-many-positional-arguments


def apply_fir(samples: numpy.ndarray, coeffs: numpy.ndarray,
              mode: ConvolveMode | None = ConvolveMode.SAME) -> numpy.ndarray:
    """Apply a filter to a signal using convolution.

    Args:
        samples: The signal to apply a filter to.
        coeffs: A 1-dimensional array of filter coefficients (AKA impulse response).
        mode: [OPTIONAL] Specifies the method of convolution.  None will result in the default mode.
    """
    # LOCAL VARIABLES
    result = None  # signal convoluted with coeffs

    # APPLY IT
    result = _call_convolve(samples=samples, coeffs=coeffs, mode=mode)

    # DONE
    return result


def create_basic_hpf(numtaps: int = 101, cutoff: float | ArrayLike = 0.25,
                     width: float | None = None, window: str | tuple = 'hamming',
                     scale: bool = True, fs: float | None = None) -> numpy.ndarray:
    """Create a basic high-pass filter, with good default values, using scipy.signal.firwin().

    See help(design_hpf) for more details on the arguments.

    Returns:
        FIR filter coefficients, AKA impulse response, in a numpy.ndarray object of
        length "numtaps".

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return design_hpf(numtaps=numtaps, cutoff=cutoff, width=width, window=window,
                      scale=scale, fs=fs)


def create_basic_lpf(numtaps: int = 101, cutoff: float | ArrayLike = 0.25,
                     width: float | None = None, window: str | tuple = 'hamming',
                     scale: bool = True, fs: float | None = None) -> numpy.ndarray:
    """Create a basic low-pass filter, with good default values, using scipy.signal.firwin().

    See help(design_lpf) for more details on the arguments.

    Returns:
        FIR filter coefficients, AKA impulse response, in a numpy.ndarray object of
        length "numtaps".

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return design_lpf(numtaps=numtaps, cutoff=cutoff, width=width, window=window,
                      scale=scale, fs=fs)


def create_rect_fir(sps: int, force_odd: bool = False) -> numpy.ndarray:
    """Create a rectangular finite infinite response (FIR) filter.

    Args:
        sps: samples per symbol.
        force_odd: [OPTIONAL] The sps value is used for the length of the taps, which probably
            should be odd.  If True, adds one to even values.

    Returns:
        Rectangular FIR filter coefficients in a numpy.ndarray.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    taps = None  # The rectangular FIR

    # INPUT VALIDATION
    validate_pos_int(sps, 'sps')
    validate_bool(force_odd, 'force_odd')

    # SETUP
    if force_odd is True and 0 == sps % 2:
        sps += 1  # Make it odd

    # CREATE IT
    taps = numpy.ones(sps, dtype=numpy.float32)
    taps /= taps.sum()

    # DONE
    return taps


def create_rrc_fir(sps: int, span: int = 8, beta: float = 1.0) -> numpy.ndarray:
    """Generate Root Raised Cosine (RRC) FIR taps.

    Args:
        sps: samples per symbol.
        span: [OPTIONAL] Length of the filter in symbols.
        beta: [OPTIONAL] Rolloff factor in [0, 1].

    Returns:
        RRC FIR filter coefficients in a numpy.ndarray.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    num = 0           # Number of sample intervals spanned by the filter
    time_vect = None  # Time vector expressed in symbol times
    taps = None       # FIR coefficients

    # INPUT VALIDATION
    validate_pos_int(sps, 'sps')
    validate_pos_int(span, 'span')
    validate_float(beta, 'beta')
    if not 0.0 <= beta <= 1.0:
        raise ValueError('The "beta" argument must be between 0 and 1, inclusive, '
                         f'instead of {beta}')

    # SETUP
    # Time vector (units of symbols)
    num = span * sps
    time_vect = numpy.arange(-num / 2, num / 2 + 1) / sps
    taps = numpy.zeros_like(time_vect)

    for index, time_val in enumerate(time_vect):
        # Special case: time_vect == 0
        if numpy.isclose(time_val, 0.0):
            taps[index] = 1.0 + beta * (4 / numpy.pi - 1)
        # Special case: |t| = T / (4β)
        elif (beta != 0 and numpy.isclose(abs(time_val), 1 / (4 * beta))):
            taps[index] = (beta / numpy.sqrt(2) * ((1 + 2 / numpy.pi)
                           * numpy.sin(numpy.pi / (4 * beta))
                           + (1 - 2 / numpy.pi) * numpy.cos(numpy.pi / (4 * beta))))
        # General case
        else:
            numerator = (numpy.sin(numpy.pi * time_val * (1 - beta)) + 4 * beta * time_val
                         * numpy.cos(numpy.pi * time_val * (1 + beta)))
            denominator = (numpy.pi * time_val * (1 - (4 * beta * time_val) ** 2))
            taps[index] = numerator / denominator
    # Normalize to unit energy
    taps /= numpy.sqrt(numpy.sum(taps**2))

    # DONE
    return taps.astype(numpy.float32)


def design_hpf(numtaps: int, cutoff: float | ArrayLike, width: float | None = None,
               window: str | tuple = 'hamming', scale: bool = True,
               fs: float | None = None) -> numpy.ndarray:
    """Design a high-pass filter using scipy.signal.firwin().

    See help(scipy.signal.firwin) for more details on the arguments.

    Args:
        numtaps: Length of the filter; must be odd.
        cutoff: Cutoff frequency of the filter.  May be a ratio (0 < cutoff < 1) if fs is None.
            Also, may be an array of cutoff frequencies (AKA band edges).
        width: [OPTIONAL] Width of the transition region expressed in the same units as fs.
        window: [OPTIONAL] Desired window to use. See `scipy.signal.get_window` for a list
            of windows and required parameters.
        scale: [OPTIONAL] If True, scale the coefficients so that the frequency response is
            exactly unity at a certain frequency.  That frequency is either:
            - 0 (DC) if the first passband starts at 0 (i.e. pass_zero is True)
            - `fs/2` (the Nyquist frequency) if the first passband ends at
              `fs/2` (i.e the filter is a single band highpass filter)
            - Otherwise, center of first passband
        fs: [OPTIONAL] The sampling frequency (AKA sample rate) of the signal in Hz.

    Returns:
        FIR filter coefficients, AKA impulse response, in a numpy.ndarray object of
        length "numtaps".

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return _call_firwin(numtaps=numtaps, cutoff=cutoff, width=width, window=window,
                        pass_zero=FIRWIN_HPF, scale=scale, fs=fs)


def design_lpf(numtaps: int, cutoff: float | ArrayLike, width: float | None = None,
               window: str | tuple = 'hamming', scale: bool = True,
               fs: float | None = None) -> numpy.ndarray:
    """Design a low-pass filter using scipy.signal.firwin().

    See help(scipy.signal.firwin) for more details on the arguments.

    Args:
        numtaps: Length of the filter.  For a lowpass filter, consider an odd number of taps.
            For all other filter types, numtaps must be odd.
        cutoff: Cutoff frequency of the filter.  May be a ratio (0 < cutoff < 1) if fs is None.
            Also, may be an array of cutoff frequencies (AKA band edges).
        width: [OPTIONAL] Width of the transition region expressed in the same units as fs.
        window: [OPTIONAL] Desired window to use. See `scipy.signal.get_window` for a list
            of windows and required parameters.
        scale: [OPTIONAL] If True, scale the coefficients so that the frequency response is
            exactly unity at a certain frequency.  That frequency is either:
            - 0 (DC) if the first passband starts at 0 (i.e. pass_zero is True)
            - `fs/2` (the Nyquist frequency) if the first passband ends at
              `fs/2` (i.e the filter is a single band highpass filter)
            - Otherwise, center of first passband
        fs: [OPTIONAL] The sampling frequency (AKA sample rate) of the signal in Hz.

    Returns:
        FIR filter coefficients, AKA impulse response, in a numpy.ndarray object of
        length "numtaps".

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    return _call_firwin(numtaps=numtaps, cutoff=cutoff, width=width, window=window,
                        pass_zero=FIRWIN_LPF, scale=scale, fs=fs)


def _call_convolve(samples: numpy.ndarray, coeffs: numpy.ndarray,
                   mode: ConvolveMode | None) -> numpy.ndarray:
    """A SPOT to call numpy.convolve().

    This function standardizes how this module validates the input to numpy.convolve()
    and calls it.  This docstring has been paraphrased/derived/interpreted from
    help(numpy.convolve).

    Args:
        samples: First one-dimensional input array.
        coeffs: Second one-dimensional input array.
        mode: If None, this kwarg will be ommitted from the function call.

    Returns:
        Discrete, linear convolution of `samples` and `coeffs`.
    """
    # LOCAL VARIABLES
    result = None                                # Discrete linear convolution of signal and coeffs
    dynamic_kwargs = {'a': samples, 'v': coeffs}  # Dynamic keyword arguments

    # INPUT VALIDATION
    validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                     must_be_complex=False)
    validate_ndarray(array=coeffs, array_name='coeffs', can_be_empty=False, num_dim=1,
                     must_be_complex=False)
    if mode is not None:
        validate_type(mode, 'mode', ConvolveMode)
        dynamic_kwargs['mode'] = mode.translate  # Translate the IntEnum to the mode string value

    # CALL IT
    result = numpy.convolve(**dynamic_kwargs)

    # DONE
    return result


def _call_firwin(numtaps: int, cutoff: float | ArrayLike, width: float | None = None,
                 window: str | tuple = 'hamming', pass_zero: bool | str = True,
                 scale: bool = True, fs: float | None = None) -> numpy.ndarray:
    """A SPOT to call scipy.signal.firwin().

    This function standardizes how this module validates the input to scipy.signal.firwin()
    and calls it.  This docstring has been paraphrased/derived/interpreted from
    help(scipy.signal.firwin).

    Args:
        numtaps: Length of the filter (number of coefficients, i.e. the filter
            order + 1).  Must be odd if the filter type is *not* a lowpass filter.
        cutoff: Cutoff frequency of filter (expressed in the same units as `fs`)
            OR an array of cutoff frequencies (that is, band edges). In the
            former case, as a float, the cutoff frequency should correspond
            with the half-amplitude point, where the attenuation will be -6dB.
            In the latter case, the frequencies in `cutoff` should be positive
            and monotonically increasing between 0 and `fs/2`. The values 0
            and `fs/2` must not be included in `cutoff`. It should be noted
            that this is different than the behavior of `scipy.signal.iirdesign`,
            where the cutoff is the half-power point (-3dB).
        width: [OPTIONAL] If `width` is not None, then assume it is the approximate width
            of the transition region (expressed in the same units as `fs`)
            for use in Kaiser FIR filter design. In this case, the `window`
            argument is ignored.
        window: [OPTIONAL] String or tuple of string and parameter values.
            Desired window to use. See `scipy.signal.get_window` for a list
            of windows and required parameters.
        pass_zero: [OPTIONAL] {True, False, 'bandpass', 'lowpass', 'highpass', 'bandstop'}.
            If True, the gain at the frequency 0 (i.e., the "DC gain") is 1.
            If False, the DC gain is 0. Can also be a string argument for the
            desired filter type (equivalent to ``btype`` in IIR design functions).
            See: constants module for FIRWIN_*F macros.
        scale: [OPTIONAL] Set to True to scale the coefficients so that the frequency
            response is exactly unity at a certain frequency.  That frequency is either:
                - 0 (DC) if the first passband starts at 0 (i.e. pass_zero is True)
                - `fs/2` (the Nyquist frequency) if the first passband ends at
                  `fs/2` (i.e the filter is a single band highpass filter);
                  center of first passband otherwise
        fs: [OPTIONAL] The sampling frequency (AKA sample rate) of the signal.
            Each frequency in `cutoff` must be between 0 and ``fs/2``.  Default is 2.

    Returns:
        FIR filter coefficients in a numpy.ndarray object of length "numtaps".

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    _validate_firwin_args(numtaps=numtaps, cutoff=cutoff, width=width, window=window,
                          pass_zero=pass_zero, scale=scale, fs=fs)
    return firwin(numtaps=numtaps, cutoff=cutoff, width=width, window=window, pass_zero=pass_zero)


def _validate_cutoff(cutoff: float | ArrayLike, cutoff_name: str, ratio: bool) -> None:
    """Validate the scipy.signal.firwin(cutoff) argument on behalf of this module.

    The dynamic validation of the cutoff is dependent on the fs value, from the perspective of
    scipy.signal.firwin().

    Args:
        cutoff: The cutoff value to validate as a float (ratio or freq.) or an
            ArrayLike object.
        cutoff_name: The name of the argument to use in Exception messages.
        ratio: If True, then the cutoff value must be > 0 and < 1.  In actual practice, any values
            > 0.99999999999999994 (4 is repeating) are rejected.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    cutoff_limit = 0.99999999999999994  # The arbitrary upper end limit for a cutoff ratio

    # INPUT VALIDATION
    validate_bool(ratio, 'ratio')
    _validate_cutoff_type(cutoff, cutoff_name)
    validate_pos_float(cutoff, cutoff_name)  # Cutoff must be positive, regardless
    if ratio:
        if cutoff > cutoff_limit:
            raise ValueError(f'As a ratio, the "{cutoff_name}" cutoff value '
                             f'"{cutoff}" *must* be < 1 (or {cutoff_limit})')


def _validate_cutoff_type(cutoff: float | ArrayLike, cutoff_name: str) -> None:
    """Validate the scipy.signal.firwin(cutoff) argument's data type on behalf of this module.

    Args:
        cutoff: The cutoff value to validate as a float or an ArrayLike object.
        cutoff_name: The name of the argument to use in Exception messages.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    is_float = True  # Track data type validation for explicitly detailed Exception message

    # VALIDATE TYPE
    # Virtually all of the GAIN.validate_*() functions check the *_name argument but, in this case,
    # I wanted to remove it as a possibility before the is-it-a-float-or-an-arraylike-or-bad check.
    validate_string(cutoff_name, 'cutoff_name', can_be_empty=False)  # Check it once
    # Float?
    try:
        validate_float(validate_this=cutoff, param_name=cutoff_name)
    except TypeError:
        is_float = False
    # ArrayLike?
    if not is_float:
        try:
            validate_arraylike(array_like=cutoff, param_name=cutoff_name, num_dim=1)
        except TypeError as err:
            raise TypeError(f'The "{cutoff_name}" argument must be a float or a '
                            '1-dimensional ArrayLike object') from err


# Placeholder for future, wiser validation
# pylint: disable=unused-argument
def _validate_firwin_args(numtaps: int, cutoff: float | ArrayLike, width: float | None = None,
                          window: str | tuple = 'hamming', pass_zero: bool | str = True,
                          scale: bool = True, fs: float | None = None) -> None:
    """Validate scipy.signal.firwin() arguments on behalf of the module.

    Args:
        See help(_call_firwin) for a description of the arguments.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # ARGUMENT VALIDATION
    validate_pos_int(validate_this=numtaps, param_name='numtaps')
    _validate_freqs(cutoff, 'cutoff', fs, 'fs')
    if width is not None:
        validate_pos_float(width, 'width')
    # Let firwin() handle the "window" argument
    # Let firwin() handle the "pass_zero" argument
    if pass_zero is not True and pass_zero is not FIRWIN_LPF:
        # It's not a lowpassfilter
        if numtaps % 2 == 0:
            raise ValueError(f'The "numtaps" value of "{numtaps}" must be odd')


def _validate_freqs(cutoff: float | ArrayLike, cutoff_name: str,
                    fs: float | None, fs_name: str) -> None:
    """Validate the scipy.signal.firwin() cutoff and fs arguments on behalf of the module.

    The cutoff and fs values are validated against each other.  The documentation for firwin() isn't
    great but observed behavior is:
    - If fs is None, then cutoff must be a ratio > 0 and < 1.  In actual practice, any values
        > 0.99999999999999994 (4 is repeating) are rejected.
    - If fs is defined, then cutoff *should* be a frequency defined in Hz.  That value should be
        > 0 and < fs/2.

    Args:
        cutoff: The cutoff value to validate as a float (ratio or freq.) or an
            ArrayLike object.
        cutoff_name: The name of the argument to use in Exception messages.
        fs: [OPTIONAL] The sampling frequency (AKA sample rate) of the signal.  Can be None.
        fs_name: The name of the argument to use in Exception messages.  Dynamically optional if
            fs is None.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    ratio = True    # Indicates whether or not cutoff must(?) be a ratio (see: help(firwin))
    nyquist = None  # fs / 2 if fs is defined

    # VALIDATE
    # fs
    if fs is not None:
        validate_string(fs_name, 'fs_name', can_be_empty=False)
        validate_float(validate_this=fs, param_name=fs_name)
        ratio = False  # The fs argument is a valid float so cutoff must(?) be defined in Hz
        nyquist = fs / 2
    # cutoff
    _validate_cutoff(cutoff=cutoff, cutoff_name=cutoff_name, ratio=ratio)
    # context
    if not ratio:
        if cutoff > nyquist or math.isclose(cutoff, nyquist):
            raise ValueError(f'The "{cutoff_name}" value ({cutoff}) must be < {nyquist} '
                             f'(which is {fs} / 2)')
