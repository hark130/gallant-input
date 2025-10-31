"""IQ capture analysis proof-of-concept PoC.

# 1. SETUP
cd Repos/gallant-input
# NOTE: Graphs will not display in a Docker container
docker run --volume "${PWD}:/app/gallant-input" --workdir /app/gallant-input -it \
    --rm gallant-input-test
pip install numpy matplotlib scipy

# 2. DO IT
python devops/scripts/PoC.py
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import correlate, welch

# 0. LOCAL VARIABLES
iq_file_1 = os.path.join(os.getcwd(), 'test', 'test_input', 'am_broadcast_02_c900k_s400k.iq')
sample_rate = 400000  # UPDATE THIS MANUALLY

# 1. LOAD THE IQ FILE
# Adjust dtype and file name to match your SDR
iq = np.fromfile(iq_file_1, dtype=np.complex64)

# 2. PLOT?
# Estimate the spectrum to find the active bandwidth
# Use FFT to find where the energy is concentrated.
# f, Pxx = welch(iq, fs=sample_rate, nperseg=4096)
f, Pxx = welch(iq, nperseg=4096)
plt.semilogy(f, Pxx)
plt.title("Power Spectral Density (Welch Estimate)")
plt.xlabel("Frequency (Hz)")
plt.ylabel("Power")
plt.show()
input('Press <Enter> to continue...')
# Compute the bandwidth
power_norm = Pxx / np.max(Pxx)
bandwidth_mask = power_norm > 0.01  # power > 1% of max
bw = f[bandwidth_mask][-1] - f[bandwidth_mask][0]
print(f"Estimated bandwidth: {bw/1e3:.1f} kHz")
input('Press <Enter> to continue...')

# 3. ESTIMATE
# Estimate center frequency offset
center_offset = (f[bandwidth_mask][0] + f[bandwidth_mask][-1]) / 2
print(f"Center offset from 0 Hz: {center_offset:.1f} Hz")
input('Press <Enter> to continue...')

# 4. DETECT MODULATION
# Detect the modulation type (basic heuristic)
# You can look at how the phase and amplitude vary over time:
amp = np.abs(iq)
phase = np.unwrap(np.angle(iq))

amp_var = np.var(amp)
phase_diff_var = np.var(np.diff(phase))

if amp_var > 0.01 and phase_diff_var < 0.01:
    mod = "AM-like"
elif amp_var < 0.01 and phase_diff_var > 0.01:
    mod = "FM or PM-like"
else:
    mod = "Complex or digital (e.g., QPSK, QAM)"
print(f"Possible modulation: {mod}")
input('Press <Enter> to continue...')
# For digital modulations, you can go deeper using clustering of the IQ constellation:
plt.scatter(np.real(iq[::100]), np.imag(iq[::100]), alpha=0.3)
plt.title("Constellation")
plt.xlabel("In-phase")
plt.ylabel("Quadrature")
plt.axis("equal")
plt.show()
input('Press <Enter> to continue...')

# 5. RATE
# Estimate symbol rate / baud rate
env = np.abs(iq - np.mean(iq))
corr = correlate(env, env, mode="full")
corr = corr[corr.size // 2:]
peaks = np.diff(np.sign(np.diff(corr))) < 0
symbol_spacing = np.mean(np.diff(np.where(peaks)[0]))
symbol_rate = sample_rate / symbol_spacing
print(f"Estimated symbol rate: {symbol_rate:.1f} baud")
input('Press <Enter> to continue...')

# 6. (Optional) Identify bursts or repetitive frames
# power = amp**2
# threshold = np.mean(power) * 2
# burst_indices = np.where(power > threshold)[0]

# # Convert to time
# burst_times = burst_indices / sample_rate
# You can then group those indices into contiguous bursts to estimate burst length and repetition
# rate.

# | Feature                     | Method                               |
# | :-------------------------- | :----------------------------------- |
# | **Center frequency**        | Spectrum centroid of active band     |
# | **Bandwidth**               | Width where PSD > threshold          |
# | **Modulation**              | Compare amplitude vs. phase variance |
# | **Symbol/baud rate**        | Envelope autocorrelation             |
# | **Bursts**                  | Power thresholding                   |
# | **Carrier drift / Doppler** | Track phase slope over time          |

# Tools to go further
# If you want more automated signal feature extraction, you can explore:

# inspectrum — interactive visualization of IQ data
# scikit-signal or liquid-dsp (C/Python bindings)
# GNU Radio + File Source block — live DSP analysis
# DeepSig / modulation classifiers — neural-network-based modulation recognition
