"""Defines functionality supporting the 'analyze' command."""

# Standard Imports
import numpy
# Third Party Imports
from scipy.signal import find_peaks, peak_widths
# Local Imports
from gallant_input.gain_sigmf.sigmfmetaparser import SigMFMetaParser
from gallant_input.spectralpeak import SpectralPeak
from gallant_input.spectrumanalysis import SpectrumAnalysis
from gallant_input.validation import (validate_ndarray, validate_pos_float_or_int, validate_pos_int,
                                      validate_type)


def analyze_spectrum(samples: numpy.ndarray, sample_rate: float | int,
                     max_peaks: int | None = None) -> SpectrumAnalysis:
    """Analyze the frequency spectrum of a sampled signal.

    Computes the Fast Fourier Transform (FFT) of the supplied real or complex samples,
    producing a frequency-domain representation of the signal. The resulting spectrum is
    analyzed to identify significant spectral peaks that may correspond to one or more transmitted
    signals.

    This function is intended to serve as the first stage of a digital receiver pipeline.
    sThe returned analysis can be used to:

        * detect signals within a wideband capture,
        * estimate carrier frequencies,
        * estimate occupied bandwidth,
        * drive frequency translation to baseband,
        * visualize the spectrum.

    The returned frequencies are centered around 0 Hz (FFT-shifted), making the results
    directly applicable to IQ baseband processing.

    This function performs analysis only. It does not modify, translate, or filter the input
    samples.

    Args:
        symbols: Real or complex-valued input samples.
        sample_rate: Sampling rate of the input samples in Hz.
        max_peaks: [OPTIONAL] The number of SpectralPeak objs to add to SpectrumAnalysis.peaks.

    Returns:
        A SpectrumAnalysis object containing:
            * FFT values
            * frequency axis
            * magnitude spectrum
            * detected spectral peaks

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    fft = None    # Shifted copy of samples where DC is moved from the to the center
    freqs = None  # Array of evenly spaced freq bins sorted in ascending order from neg to pos freqs
    mag = None    # The element-wise absolute value of the FFT bins
    peaks = None  # An array of peak indices
    props = None  # Dictionary of properties containing metadata about each peak

    # INPUT VALIDATION
    validate_ndarray(array=samples, array_name='samples', can_be_empty=False,
                     num_dim=1, must_be_complex=False)
    validate_pos_float_or_int(validate_this=sample_rate, param_name='sample_rate')
    if max_peaks is not None:
        validate_pos_int(max_peaks, 'max_peaks')

    # ANALYSZE IT
    fft = numpy.fft.fftshift(numpy.fft.fft(samples))  # FFT bins
    freqs = numpy.fft.fftshift(numpy.fft.fftfreq(len(samples), d=1/sample_rate))  # Frequencies
    mag = numpy.abs(fft)  # Magnitude of the FFT bins
    peaks, props = find_peaks(mag, prominence=numpy.max(mag) * 0.10)
    # print(f'PEAKS: {peaks}')  # DEBUGGING
    # print(f'PROPS: {props}')  # DEBUGGING

    # STORE IT
    left_ips, right_ips = _calc_width(mag, peaks)
    spectral_peaks = [SpectralPeak(frequency=freqs[peak], magnitude=mag[peak],
                                   prominence=props["prominences"][i],
                                   left_edge=numpy.interp(left_ips[i], numpy.arange(len(freqs)),
                                                          freqs),
                                   right_edge=numpy.interp(right_ips[i], numpy.arange(len(freqs)),
                                                           freqs), bucket=peak)
                      for i, peak in enumerate(peaks)]  # Construct *all* the peaks
    spectral_peaks.sort(key=lambda peak: peak.magnitude, reverse=True)
    if max_peaks is not None:
        spectral_peaks = spectral_peaks[:max_peaks]  # Remove unwanted peaks
    spectral_peaks.sort(key=lambda peak: peak.frequency)  # Sort remnants by frequency

    # DONE
    return SpectrumAnalysis(fft=fft, frequencies=freqs, magnitudes=mag, peaks=spectral_peaks)


def print_signal_parameters(meta_obj: SigMFMetaParser) -> None:
    """Print signal parameters from the provided SigMFMetaParser object.

    Args:
        meta_obj: SigMFMetaParser object constructed from the sigmf-meta file in question.

    Raises:
        FileNotFoundError: The underlying file is not found.
        KeyError: Invalid or missing key.
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES
    low_freq = None   # Frequency lower edge as a float
    high_freq = None  # Frequency upper edge as a float

    # INPUT VALIDATION
    validate_type(var=meta_obj, var_name='meta_obj', var_type=SigMFMetaParser)

    # PRINT IT
    # Center frequency
    print(f'Center Frequency: {meta_obj.get_center_freq()} Hz')
    # Bandwidth
    print(f'Bandwidth: {meta_obj.get_bandwidth()} Hz')
    # Frequency deviation
    (low_freq, high_freq) = meta_obj.determine_freq_range()
    print(f'Frequency Deviation\n\tLow:  {low_freq} Hz\n\tHigh: {high_freq} Hz')
    # Burst length in symbols and seconds
    # Baud rate and bit rate
    # Preambles and Postambles
    # Repetitive segments
    # Consistent and variable data fields


def _calc_width(mag: numpy.ndarray, peaks: numpy.ndarray, rel_height: float = 0.5) -> Tuple:
    """Calculate the bandwidth of the peaks."""
    widths, heights, left_ips, right_ips = peak_widths(mag, peaks, rel_height=rel_height)
    return (left_ips, right_ips)
