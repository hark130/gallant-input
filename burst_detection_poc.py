"""Trying some burst detection techniques on a FHSS capture.

USAGE:
    python burst_detection_poc.py
"""

# Standard Imports
from enum import auto, Enum
from pathlib import Path
from typing import Final, List, NamedTuple, Tuple
import math
# Third Party Imports
from burst_detection import burst_detection, enumerate_bursts
from neurodsp.burst import detect_bursts_dual_threshold
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
# Local Imports
from burst_corpus import BurstCorpus, BurstRecord, save_corpus
from burst_detector import Burst, BurstDetector
from channel_plan import ChannelMatch, ChannelPlan, FhssProfile, HopPattern
from frequency_estimator import CentroidFrequencyEstimator
from gallant_input.io import read_samples
from gallant_input.modem.calc import calculate_sps
from gallant_input.plot import plot_spectrum, plot_symbol_boundaries, plot_time_domain
from gallant_input.signal import (compute_magnitude_spectrum, convert_mag_to_db, decimate_samples,
                                  downconvert_signal)
from gallant_input.synch.timing import recover_clock_mm
from noise_floor_tracker import NoiseFloorTracker
from rxtx.static_rx_fhss import build_modem, build_modem_config

CENTER_FREQ: Final[float] = 915e6
FILENAME: Final[Path] = Path() / "data" / "fhss_915mhz_26msps.iq"
MIN_WINDOW_SYMS: Final[float] = 1.0  # An envelope null lasts about one symbol
SAMPLE_RATE: Final[float] = 26e6
SYMBOL_RATE: Final[float] = 250_000  # 250kbd (or is it encoded and actually 125kbd?!)
# MIN_BURST_SEC: Final[float] = 7.5e-6  # Shortest burst: 0.0075 ms
# MIN_GAP_SEC: Final[float] = 0.75e-6   # Shortest gap: 0.00075 ms
MIN_BURST_SEC: Final[float] = 7.5e-3  # Shortest burst: 7.5 ms
MIN_GAP_SEC: Final[float] = 0.75e-3   # Shortest gap: 0.75 ms
MIN_NOISE_FLOOR: Final[float] = 1e-12  # Keeps the floor (and thresholds built on it) above zero
FLOOR_TAU_SEC: Final[float] = 0.1  # Noise-floor tracking time constant (s)
OFF_DB: Final[float] = 4.0         # Burst stops below this many dB above the noise floor
ON_DB: Final[float] = 8.0          # Burst starts above this many dB above the noise floor
TRAIN_SEC: Final[float] = 50e-3    # Noise-floor training time (s); > 2x any burst inside it
# FHSS MACROS
FIRST_CHANNEL_FREQ: Final[float] = 905e6  # Hz, center of the lowest channel
NUM_CHANNELS: Final[int] = 50             # From my notes
CHANNEL_SPACING: Final[float] = 350e3     # Hz, from my notes
GAP_HIGH_FREQ: Final[float] = 916.60e6    # First channel above the gap (channel 26)
GAP_LOW_FREQ: Final[float] = 913.40e6     # Last channel below the gap (channel 25)
# Channel numbers, in hop order
HOP_PATTERN: Final[Tuple[int, ...]] = (
    13,35,27,41,44,30,34,18,31,28,17,47,36,33,7,16,9,43,20,15,5,45,8,24,42,
    32,40,38,39,4,37,14,1,50,3,46,6,26,49,19,25,21,12,11,22,48,23,10,29,2)
TRAIN_PERCENTILE: Final[float] = 10.0  # Busy band: >= 10% noise
CORPUS_FILENAME: Final[Path] = Path() / "data" / "fhss_corpus.json"
FSK_DEV_HZ: Final[float] = 127_000  # FSK Tone Deviation in Hz (full distance, peak-to-peak)


def compute_window_size(samp_rate: float, symbol_rate: float, min_burst_syms: int,
                        min_gap_syms: int, target_syms: int = 4,
                        max_fraction: float = 0.25) -> int:
    """Choose the moving-average window (samples) for an envelope burst detector.

    Args:
        samp_rate: Capture sample rate, in samples per second.
        symbol_rate: Protocol symbol rate, in symbols per second (baud).
        min_burst_syms: Shortest burst the protocol can send, in symbols.
        min_gap_syms: Shortest silence between bursts, in symbols.
        target_syms: [OPTIONAL] Preferred window length, in symbols.
        max_fraction: [OPTIONAL] Largest window allowed, as a fraction of the shortest
            burst or gap.

    Returns:
        The window size in samples.

    Raises:
        ValueError: Bad value, or the specifications leave no valid window size.
    """
    # LOCAL VARIABLES
    sps = 0.0   # Samples per symbol
    lower = 0   # Smallest window that bridges an envelope null (samples)
    upper = 0   # Largest window that still resolves the shortest burst or gap (samples)
    window = 0  # Chosen window size (samples)

    # INPUT VALIDATION
    if samp_rate <= 0 or symbol_rate <= 0:
        raise ValueError('samp_rate and symbol_rate must be positive')
    if min(min_burst_syms, min_gap_syms, target_syms) < 1:
        raise ValueError('Symbol counts must be >= 1')
    if not 0 < max_fraction <= 1:
        raise ValueError(f'max_fraction must be in (0, 1], got {max_fraction}')

    # SIZE IT
    sps = samp_rate / symbol_rate
    lower = math.ceil(MIN_WINDOW_SYMS * sps)
    upper = math.floor(max_fraction * min(min_burst_syms, min_gap_syms) * sps)
    if lower > upper:
        raise ValueError(f'No valid window: need >= {lower} samples to bridge nulls, but '
                         f'<= {upper} samples to resolve the shortest burst or gap')
    window = min(max(round(target_syms * sps), lower), upper)

    # DONE
    return window


def demodulate_burst(burst: np.ndarray, sample_rate: float | int,
                     symbol_rate: float | int, debug: bool = False) -> str:
    """Demodulate a sliced burst and return the binary as a string.

    Args:
        burst: The sliced burst of samples to demodulate.
        sample_rate: The sample rate of the capture in samples per second.
        symbol_rate: The number of symbols-per-second (1 / symbol time).
    """
    # LOCAL VARIABLES
    binary: str = ""  # Demodulated binary bytes converted to a string
    sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Samples-per-symbol
    config = build_modem_config(sample_rate=sample_rate, symbol_rate=symbol_rate,
                                freq0=-FSK_DEV_HZ/2, freq1=FSK_DEV_HZ/2)
    modem = build_modem(config=config)
    decimate = 8           # Decimation (e.g., 1 to skip decimation)
    metric = None          # Instantaneous frequency measurements
    symbol_metrics = None  # Soft symbols
    symbols = None         # Binary bytes

    # PREPARE
    if decimate > 1:
        burst = decimate_samples(samples=burst, decimate=decimate)
        sample_rate = sample_rate / decimate  # Update the sample rate
        sps = calculate_sps(sample_rate=sample_rate, symbol_rate=symbol_rate)  # Calc new sps
    if sps > 20 and arg_vals.debug:
        print(f'Consider decimating the samples-per-symbol, currently "{sps}", below 20')

    # DEMODULATE IT
    # NOTE TO FUTURE HARK... UN-GAIN THIS IMPLEMENTATION BY USING A BETTER DEMOD/TIMING SYNCH
    # Step 1 - Demod to Metrics
    metric = modem.demodulate_to_metric(samples=burst)
    if debug:
        plot_time_domain(samples=metric, samp_rate=sample_rate,
                         title='Time Domain (Demod Step 1: Metrics)', now=False)
        plot_symbol_boundaries(real_wave=metric, sps=sps,
                               title='Symbol Boundaries (Demod Step 1: Metrics)', now=False)
    # Step 2 - Time Sync w/ Interpolation(?)
    # symbol_metrics = recover_clock_mm(metric, sps, interp=None)  # Do not interpolate
    symbol_metrics = recover_clock_mm(metric, sps, interp=16)  # Interp for better boundary
    if debug:
        plot_time_domain(samples=symbol_metrics, samp_rate=sample_rate,
                         title='Time Domain (Demod Step 2: Symbol Metrics)', now=False)
        plot_symbol_boundaries(real_wave=symbol_metrics, sps=1,
                               title='Symbol Boundaries (Demod Step 2: Symbol Metrics)',
                               now=False)
    # Step 3 - Symbol Decisions
    symbols = modem.decide_symbols(symbol_metrics=symbol_metrics)
    # Step 4 - Convert binary bytes to a string
    binary = symbols.decode("ascii")
    if debug:
        plt.show()  # Plot them all *now*
        exit()  # TESTING

    # DONE
    return binary


def detect_bursts_1(samples: np.ndarray, sample_rate: float) -> None:
    """Method 1: Dual-Amplitude Threshold (Common for Oscillations & Neural Data)."""
    
    # 1. Convert complex samples to real-valued magnitude
    real_samples = np.abs(samples)  
    
    # 2. Match exact neurodsp variable signatures
    dual_thresh = (3.5, 25.0)       
    f_range = (10, 40)              
    min_n_cycles = None             # Turned off to let duration take priority
    min_burst_duration = 0.005      # Explicit burst duration limit in seconds

    # 3. Call the function using exact official keyword arguments
    is_burst = detect_bursts_dual_threshold(
        real_samples, 
        fs=sample_rate,
        dual_thresh=dual_thresh,       # Verified keyword name
        f_range=f_range,               # Verified keyword name
        min_n_cycles=min_n_cycles,     # Verified keyword name (None instead of 0)
        min_burst_duration=min_burst_duration  # Verified keyword name
    )
    
    print(f"Success! Detected burst states across {len(is_burst)} samples.")
    # You can now use 'is_burst' (a boolean array) to plot or extract your pulses.
    print(f"IS BURST: {is_burst}")
    # Adjust start_sec to wherever your burst actually sits in the file
    # plot_burst_verification(samples, is_burst, sample_rate, start_sec=1.5, duration_sec=0.5)
    plot_burst_verification(samples, is_burst, sample_rate, start_sec=0.0, duration_sec=2.0)
    extract_burst_metadata(is_burst, sample_rate)


def detect_bursts_2(samples: np.ndarray) -> None:
    """Method 2: Sliding Standard Deviation (Ad-Hoc / Real-Time).

    For streaming or general-purpose spectrum analysis, you can slide a window across time bins
    and flag a burst when the change relative to the rolling standard deviation exceeds a set
    multiple.
    """
    # Assuming 'samples' is a 1D array of power at a specific frequency over time
    window_size = 50
    s = pd.Series(samples)
    rolling_mean = s.rolling(window_size).mean()
    rolling_std = s.rolling(window_size).std()

    z_score = (s - rolling_mean) / rolling_std
    burst_indices = np.where(z_score > 3.0)[0]  # Threshold at 3 standard deviations
    print(f"BURST INDICES: {burst_indices}")


def detect_bursts_3(samples: np.ndarray) -> None:
    """Method 3: Kleinberg’s Burst Detection (For Event/Stream Counts).

    If your "spectrum" is represented as discrete event counts or energy spikes over time,
    Kleinberg’s state-transition model treats bursts as a shift from a baseline state to a denser
    "bursty" state.
    """
    # r: target event counts, d: total events per time bin
    q, r, d = burst_detection(r_counts, d_counts, s=2, gamma=1)
    bursts_df = enumerate_bursts(q, r, d)
    print(f"BURSTS DF: {bursts_df}")


def extract_burst_metadata(is_burst, sample_rate):
    """Finds the precise start, stop, and duration of every single burst event."""
    # Convert boolean to integers (0 and 1)
    is_burst_int = is_burst.astype(int)
    
    # Find edges: +1 means transitioned False -> True (Start), -1 means True -> False (End)
    edges = np.diff(is_burst_int)
    starts = np.where(edges == 1)[0] + 1
    ends = np.where(edges == -1)[0] + 1
    
    # Handle edge case where file starts or ends mid-burst
    if is_burst[0]:
        starts = np.insert(starts, 0, 0)
    if is_burst[-1]:
        ends = np.append(ends, len(is_burst) - 1)
        
    print(f"\n--- Burst Statistics Report ---")
    print(f"Total Unique Bursts Found: {len(starts)}")
    
    # Print out details for the first 10 bursts found
    for i, (start_idx, end_idx) in enumerate(zip(starts[:10], ends[:10])):
        start_time = start_idx / sample_rate
        end_time = end_idx / sample_rate
        duration = end_time - start_time
        print(f"Burst #{i+1}: Start={start_time:.4f}s | End={end_time:.4f}s | "
              f"Duration={duration*1000:.2f} ms")


def plot_burst_verification(samples, is_burst, sample_rate, start_sec=2.0, duration_sec=0.5):
    """Plots a subset of the signal magnitude with burst events highlighted."""
    # Convert seconds to sample indices
    start_idx = int(start_sec * sample_rate)
    end_idx = start_idx + int(duration_sec * sample_rate)
    
    # Slice the data
    time_vector = np.arange(start_idx, end_idx) / sample_rate
    magnitude_subset = np.abs(samples[start_idx:end_idx])
    mask_subset = is_burst[start_idx:end_idx]
    
    plt.figure(figsize=(12, 5))
    
    # 1. Plot the raw envelope magnitude
    plt.plot(time_vector, magnitude_subset, label='Signal Magnitude', color='blue', alpha=0.7)
    
    # 2. Highlight where bursts are active
    # fill_between highlights regions where mask_subset is True
    plt.fill_between(time_vector, 0, np.max(magnitude_subset), where=mask_subset, 
                     facecolor='red', alpha=0.3, label='Detected Burst')
    
    plt.title(f'Burst Detection Analysis Window ({start_sec}s to {start_sec + duration_sec}s)')
    plt.xlabel('Time [Seconds]')
    plt.ylabel('Magnitude')
    plt.legend(loc='upper right')
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.tight_layout()
    plt.show()


def save_bursts_as_corpus(samples: np.ndarray, window: int, min_len: int, bursts: List[Burst],
                          matches: List[ChannelMatch],
                          filename: Path | str = CORPUS_FILENAME) -> None:
    """Save burst details, with respect to a FHSS hop pattern, to a corpus for offline analysis.

    Args:
        window: Moving-average length (samples) used to smooth the envelope in the burst detector.
        min_len: Minimum length of a valid burst.
        bursts: A list of detected bursts.
        matches: A list of matches against a ChannelPlan (see: FHSS hop pattern).
        filename: [OPTIONAL] The output filename for the JSON corpus.
    """
    _burst = None  # The downconverted samples sliced out of the samples array
    corpus = BurstCorpus(capture=filename, samp_rate=SAMPLE_RATE, center_freq=CENTER_FREQ,
                         symbol_rate=SYMBOL_RATE,
                         params={"on_db": ON_DB, "off_db": OFF_DB, "window": window,
                                 "min_len": min_len, "train_percentile": TRAIN_PERCENTILE,
                                 "channel_spacing": CHANNEL_SPACING})
    for number, (burst, match) in enumerate(zip(bursts, matches), start=1):
        _burst = samples[burst.start:burst.stop]
        if match.residual_hz != 0.0:
            _burst = downconvert_signal(samples=_burst, sample_rate=SAMPLE_RATE,
                                        center_freq=-match.residual_hz)  # Downconvert to baseband
        _binary = demodulate_burst(burst=_burst, sample_rate=SAMPLE_RATE, symbol_rate=SYMBOL_RATE,
                                   debug=True,  # DEBUGGING
                                   )
        corpus.add_record(BurstRecord(number=number, start=burst.start, stop=burst.stop,
                                      channel=match.channel,
                                      freq_hz=match.channel_freq + match.residual_hz,
                                      residual_hz=match.residual_hz,
                                      # bits=demodulate_burst(...)))  # Your rxtx demod
                                      # bits="01010101"))  # PLACEHOLDER
                                      bits=_binary))
    save_corpus(corpus, filename)


def main():
    """do_it()."""
    samples = read_samples(filename=FILENAME)
    offset_hz = 0.0  # Offset from the center frequency to identify channel bursts
    # burst_thresh = -40  # Burst mag threshold in dB
    # burst_thresh = -45  # Burst mag threshold in dB
    # burst_thresh = -50  # Burst mag threshold in dB
    min_len = round(SAMPLE_RATE * MIN_BURST_SEC)  # Minimum length for valid bursts
    floor_tracker = NoiseFloorTracker(train_len=round(SAMPLE_RATE * TRAIN_SEC),
                                      alpha=1 / (SAMPLE_RATE * FLOOR_TAU_SEC),
                                      train_percentile=TRAIN_PERCENTILE)
    window = compute_window_size(samp_rate=SAMPLE_RATE, symbol_rate=SYMBOL_RATE,
                                 min_burst_syms=(SYMBOL_RATE / MIN_BURST_SEC),
                                 min_gap_syms=(SYMBOL_RATE / MIN_GAP_SEC))
    detector = BurstDetector(floor_tracker=floor_tracker, on_db=ON_DB, off_db=OFF_DB,
                             window=window, min_len=min_len)
    chunk_size = 10_000
    act_min_burst_time = 100_000  # Actual shortest burst time
    # NOTE: This channel construction assumed channel numbering 0-49
    # channels = {ch: GAP_LOW_FREQ - (25 - ch) * CHANNEL_SPACING for ch in range(0, 26)}
    # channels.update({ch: GAP_HIGH_FREQ + (ch - 26) * CHANNEL_SPACING for ch in range(26, 50)})
    # Channel Numbering
    channels = {ch: GAP_LOW_FREQ - (25 - ch) * CHANNEL_SPACING for ch in range(1, 26)}
    channels.update({ch: GAP_HIGH_FREQ + (ch - 26) * CHANNEL_SPACING for ch in range(26, 51)})
    plan = ChannelPlan(channels)
    profile = FhssProfile(plan=plan, pattern=HopPattern(HOP_PATTERN))
    # plot_spectrum(samples=samples, samp_rate=SAMPLE_RATE,
    #               center_freq=CENTER_FREQ, title="FHSS Spectrum")
    # plot_time_domain(samples=samples, samp_rate=SAMPLE_RATE, title="FHSS Time (Complex)")
    # plot_time_domain(samples=np.abs(samples), samp_rate=SAMPLE_RATE, title="FHSS Time (Real)")
    # detect_bursts_1(samples=samples, sample_rate=SAMPLE_RATE)
    # detect_bursts_2(samples)

    # DETECT BURSTS
    # Good visual plot
    # plot_time_domain(samples=np.abs(samples), samp_rate=SAMPLE_RATE, title="FHSS Time (Real)")

    # Chunk it
    samples_seen = 0  # Samples fed to the detector so far
    for chunk in np.array_split(samples, np.arange(chunk_size, len(samples), chunk_size)):
        detector.detect_chunk(chunk=chunk)
        # Troubleshooting (initially) missed bursts
        # samples_seen += chunk.size
        # floor = floor_tracker.get_floor()
        # if floor is not None:
        #     print(f"{samples_seen / SAMPLE_RATE:.3f} s  floor {20 * np.log10(floor):.1f} dB")
    detector.flush()  # Close a burst still open at end of file
    print(f"BURSTS:")
    burst_num = 0
    estimator = CentroidFrequencyEstimator()
    bursts = detector.get_bursts()
    matches = []
    # Pass 1: measure and resolve every burst
    for burst in bursts:
        burst_num += 1
        start_time = burst.start/SAMPLE_RATE
        stop_time = burst.stop/SAMPLE_RATE
        duration = (burst.stop - burst.start) / SAMPLE_RATE
        if duration > 0:
            act_min_burst_time = min(act_min_burst_time, duration)
        offset_hz = estimator.estimate(samples[burst.start:burst.stop], SAMPLE_RATE)
        matches.append(profile.plan.resolve(CENTER_FREQ + offset_hz,
                                            max_residual_hz=CHANNEL_SPACING / 2))
        # OUTPUT
        # print(f"{burst_num:>3}: {burst.start} --> {burst.stop}")  # Printing indices
        # print(f"{burst_num:>3}: {burst.start/SAMPLE_RATE} --> {burst.stop/SAMPLE_RATE}")  # Raw
        # print(f"{burst_num:>3}: {start_time} --> {stop_time} "
        #       f"(time {duration} s)")  # SPOT
        # print(f"{burst_num:>3}: {start_time} --> {stop_time} (time {duration} s) "
        #       f"freq {(CENTER_FREQ + offset_hz) / 1e6:.4f} MHz")  # FULL output
        # print(f"{burst_num:>3}: {(CENTER_FREQ + offset_hz) / 1e6:.4f} MHz")  # FHSS hops

    # Pass 2: align against the hop pattern, then report
    alignment = profile.pattern.align([match.channel for match in matches])
    for burst_num, (burst, match, expected, hit) in enumerate(
            zip(bursts, matches, alignment.expected, alignment.matches), start=1):
        print(f"{burst_num:>3}: {burst.start / SAMPLE_RATE:.6f} s  ch {match.channel}  "
              f"(expected {expected})  residual {match.residual_hz / 1e3:+7.1f} kHz  "
              f"{'OK' if hit else 'MISMATCH'}")
    print(f"Matched {alignment.num_matched} of {len(bursts)} at pattern offset "
          f"{alignment.offset}")
    # print(f"Shortest burst time: {act_min_burst_time} s")

    # Save the corpus
    save_bursts_as_corpus(samples=samples, window=window, min_len=min_len, bursts=bursts,
                          matches=matches)


if __name__ == "__main__":
    main()
