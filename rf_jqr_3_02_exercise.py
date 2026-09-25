"""RF JQR 3.02 exercise.py

Original module docstring:
"Don't worry, I intentionally made the code below messy so it would be very hard to tell what the
 frequency offset is :)"

EXERCISE:
"In the first half of exercise.py, I've generated a BPSK signal with a frequency offset.
 To find the frequency offset, you can square the signal in order to cluster the distinct symbol
 groupings on the constellation plot. See the visualization here:
    https://ventrella.com/ComplexSquaring/.
 Now that you are adept at complex number arithmetic, square the signal and determine the
 frequency offset. What is it?"
"Implement quadrature demodulation: https://wiki.gnuradio.org/index.php/Quadrature_Demod.
 It is an angle of the product of a one-sample delayed &conjugated input and the original
 undelayed input."

USAGE:
    python rf_jqr_3_02_exercise.py
"""

# Standard Imports
from typing import Final
# Third Party Imports
import matplotlib.pyplot as plt
import numpy as np
from scipy import signal
# Local Imports

SAMPLE_RATE: Final[int] = 1e6  # Sample rate being used here
SAMPLES_PER_SYMBOL: Final[int] = 8  # Samples per symbol being used here


def determine_bpsk_freq_offset(samples: np.ndarray, sample_rate: int) -> float:
    """Calculate the freq offset by clustering a bpsk signal and measuring the rate of angle change.

    1. Cluster the diagram by squaring it
    2. Measure the angle change between samples
    3. Calculate the average phase change
    4. Divide that result by 2 because squaring the samples doubled the frequency offset

    Returns:
        The frequency offset.
    """
    squared = np.square(samples)  # Clustered
    diffs = squared[1:] * np.conj(squared[:-1])  # Combined vectors of squared[n] and squared[n+1]
    mean_diff = np.mean(diffs)  # Average of the combined vectors
    average_phase_delta = np.angle(mean_diff)  # Average change in frequency
    return average_phase_delta / 2   # (e^theta)^2 == e^2theta


def correct_freq(samples: np.ndarray, freq_offset: float) -> np.ndarray:
    """Correct the frequency offset of samples by freq_offset.

    Returns:
        The samples array with a corrected frequency.
    """
    time = np.arange(len(samples))  # An array of time indices
    return samples * np.exp(-1j * freq_offset * time)  # Correct the frequency over time


def get_bpsk_signal(sample_rate: int) -> np.ndarray:
    """Original exercise.py code, to generate the signal, wrapped in a function."""
    num_symbols = 100
    sps = SAMPLES_PER_SYMBOL  # Originally sps = 8
    fs = sample_rate  # Originally fs = 1e6
    bits = np.random.randint(0, 2, num_symbols)
    pulse_train = np.array([])
    for bit in bits:
        pulse = np.zeros(sps)
        pulse[0] = bit * 2 - 1
        pulse_train = np.concatenate((pulse_train, pulse))
    original_data = pulse_train
    num_taps = 101
    beta = 0.35
    Ts = sps
    t = np.arange(-51, 52)
    h = np.sinc(t / Ts) * np.cos(np.pi * beta * t / Ts) / (1 - (2 * beta * t / Ts) ** 2)
    samples = np.convolve(pulse_train, h)
    delay = 0.4
    N = 21
    n = np.arange(N)
    h = np.sinc(n - (N - 1) / 2 - delay)
    h *= np.hamming(N)
    h /= np.sum(h)
    samples = np.convolve(samples, h)
    fo = 300
    Ts = 1 / fs
    t = np.arange(0, Ts * len(samples), Ts)
    samples = samples * np.exp(1j * 2 * np.pi * fo * t)
    return samples


def plot_bpsk_signal(samples: np.ndarray, fs: int,
                     title1: str = 'PSD of BPSK Signal with freq offset',
                     title2: str = 'BPSK Constellation - with freq offset') -> None:
    """Original exercise.py code, to plot the signal, wrapped in a function."""
    # show that we have a BPSK signal with a frequency offset
    fig, axes_1 = plt.subplots(1, figsize=(7, 4))
    psd = np.fft.fftshift(np.abs(np.fft.fft(samples)))
    f = np.linspace(-fs / 2.0, fs / 2.0, len(psd))
    axes_1.set_xlabel('frequency (Hz)')
    axes_1.set_ylabel('power')
    axes_1.set_title(title1)
    axes_1.plot(f, psd)
    fig, axes_2 = plt.subplots(1, figsize=(5, 5))
    plt.scatter(np.real(samples[5::8]), np.imag(samples[5::8]), marker='o')
    plt.title(title2)
    plt.xlabel('real')
    plt.ylabel('imag')
    plt.show()


def print_freq_offset_hz(radian_offset: float, sample_rate: int) -> None:
    """Convert and print the frequency offset in human-readable Hz."""
    freq_offset_hz = radian_offset * sample_rate / (2 * np.pi)
    print(f'The frequency offset is {freq_offset_hz} Hz')


def main() -> None:
    """do_it()."""
    sample_rate = SAMPLE_RATE
    samples = get_bpsk_signal(sample_rate=SAMPLE_RATE)
    plot_bpsk_signal(samples=samples, fs=SAMPLE_RATE)
    freq_offset = determine_bpsk_freq_offset(samples=samples, sample_rate=sample_rate)
    print(f'The frequency offset is {freq_offset} radians')
    print_freq_offset_hz(freq_offset, sample_rate)
    new_samples = correct_freq(samples=samples, freq_offset=freq_offset)
    freq_offset = determine_bpsk_freq_offset(samples=new_samples, sample_rate=sample_rate)
    print(f'The NEW frequency offset is {freq_offset} radians')
    print_freq_offset_hz(freq_offset, sample_rate)
    plot_bpsk_signal(samples=new_samples, fs=SAMPLE_RATE,
                     title1='PSD of BPSK Signal with corrected freq',
                     title2='BPSK Constellation - with corrected freq')


if __name__ == '__main__':
    main()
