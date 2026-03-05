"""Implement FIR/IIR filters."""

# Standard Imports
# Third Party Imports
from numpy.typing import ArrayLike
from scipy.signal import firwin
# Local Imports
from gallant_input.validation import validate_pos_int


def design_lpf(numtaps: int, cutoff: float | ArrayLike, width: float | None = None,
               window: string | tuple = 'hamming', pass_zero: bool | string = True,
               scale: bool = True, fs: float | None = None) -> numpy.ndarray:
    """Design a low-pass filter using scipy.signal.firwin().

    See help(scipy.signal.firwin) for more details on the arguments.

    Args:
        numtaps: Length of the filter.
        cutoff: Cutoff frequency of the filter.  May be a ratio (0 < cutoff < 1) if fs is None.
            Also, may be an array of cutoff frequencies (AKA band edges).
        width: [OPTIONAL] Width of the transition region expressed in the same units as fs.
        window: [OPTIONAL] Desired window to use. See `scipy.signal.get_window` for a list
            of windows and required parameters.
        pass_zero: [OPTIONAL] If True, the gain at the frequency 0 is 1.  If False, the DC
            gain is 0. Can also be a string argument for the desired filter type.
            See help(scipy.signal.firwin) for supported strings.
        scale: [OPTIONAL] If True, scale the coefficients so that the frequency response is
            exactly unity at a certain frequency.  That frequency is either:
            - 0 (DC) if the first passband starts at 0 (i.e. pass_zero is True)
            - `fs/2` (the Nyquist frequency) if the first passband ends at
              `fs/2` (i.e the filter is a single band highpass filter)
            - Otherwise, center of first passband
        fs: [OPTIONAL] The sampling frequency (AKA sample rate) of the signal in Hz.
    """
    return _call_firwin(numtaps=numtaps, cutoff=cutoff, width=width, window=window,
                        pass_zero=pass_zero, scale=scale, fs=fs)


def _call_firwin(numtaps: int, cutoff: float | ArrayLike, width: float | None = None,
                 window: string | tuple = 'hamming', pass_zero: bool | string = True,
                 scale: bool = True, fs: float | None = None) -> numpy.ndarray:
    """A SPOT to call scipy.signal.firwin().

    This function standardizes how this module validates the input to scipy.signal.firwin()
    and calls it.  This docstring has been paraphrased/derived/interpreted from
    help(scipy.signal.firwin).

    Args:
        numtaps: Length of the filter (number of coefficients, i.e. the filter 
            order + 1).  Must be odd if a passband includes the Nyquist frequency.
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
                          pass_zero=pass_zero)
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
    
    """
    # LOCAL VARIABLES
    cutoff_limit = 0.99999999999999994  # The arbitrary upper end limit for a cutoff ratio

    # INPUT VALIDATION
    validate_type(var=ratio, var_name='ratio', var_type=bool)
    validate_string(cutoff_name, 'cutoff_name', can_be_empty=False)
    try:
        validate_float(validate_this=cutoff, param_name=cutoff_name)
    except TypeError:
        validate_arraylike(array_like=cutoff, param_name=cutoff_name, num_dim=1)
    else:
        if ratio:
            validate_pos_float(cutoff, cutoff_name)
            # if cutoff <= 0 and math.isclose(cutoff, 0, abs_tol=1e-9):
            #     raise ValueError(f'As a ratio, the "{cutoff_name}" cutoff value '
            #                      f'"{cutoff}" *must* be > 0')
            if cutoff > 0.99999999999999994:
                raise ValueError(f'As a ratio, the "{cutoff_name}" cutoff value '
                                 f'"{cutoff}" *must* be < 1')


def _validate_firwin_args(numtaps: int, cutoff: float | ArrayLike, width=None, window='hamming',
                          pass_zero=True, scale=True, fs=None) -> None:
    """Validate scipy.signal.firwin() arguments on behalf of the module.

    Args:
        See help(_call_firwin) for a description of the arguments.
    """
    # ARGUMENT VALIDATION
    validate_pos_int(validate_this=numtaps, param_name='numtaps')
    _validate_freqs(cutoff, 'cutoff', fs, 'fs')
    if width is not None:
        validate_pos_float(width, 'width')
    # Let firwin() handle the "window" argument
    # Let firwin() handle the "pass_zero" argument


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
    """
    # LOCAL VARIABLES
    ratio = True  # Indicates whether or not cutoff must(?) be a ratio (see: help(firwin))

    # VALIDATE
    # fs
    if fs is not None:
        validate_string(fs_name, 'fs_name', can_be_empty=False)
        validate_float(validate_this=fs, param_name=fs_name)
        ratio = False  # The fs argument is a valid float so cutoff must(?) be defined in Hz
    # cutoff
    _validate_cutoff(cutoff=cutoff, cutoff_name=cutoff_name, ratio=ratio)
