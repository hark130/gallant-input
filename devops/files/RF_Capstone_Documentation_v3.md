# RF Capstone v3 Documentation

**Project:** `gallant-input` / `rf_capstone_v3.py`
**Hardware:** Ettus Research USRP B200 series (tested on B206mini and B205mini)

1. [System-Architecture Document](#part-1-system-architecture-document)
2. [Operational Documentation](#part-2-operational-documentation)

---

# PART 1: SYSTEM-ARCHITECTURE DOCUMENT

## 1.1 Overview

This system implements a bidirectional, two-user, point-to-point RF link over a single
frequency band using Binary Frequency Shift Keying (BFSK).  Each user transmits and
receives on a dedicated USRP B200-series SDR.  The protocol splits the band into two channels,
one per user, so both users can transmit and receive simultaneously via Frequency Division Duplexing (FDD).

| Parameter | Value | Source |
|---|---|---|
| Modulation | 2-FSK (BFSK), continuous-phase, Gaussian-filtered (GFSK, BT=0.4) | `gallant_input.modem.fsk2.FSK2`, `rf_capstone_v3.py`'s `GFSK_BT` |
| Center frequency (reference) | 912.050 MHz | `rf_capstone_v3.py`'s `CENTER_FREQ` |
| Sample rate | 240 kHz | `rf_capstone_v3.py`'s `SAMPLE_RATE` |
| Symbol rate | 2400 baud | `rf_capstone_v3.py` `SYMBOL_RATE` |
| Samples per symbol (sps) | 100 | Derived from the sample_rate / symbol_rate |
| Tone separation (deviation) | 4800 Hz (-/+2400 Hz around each user's center) | `rf_capstone_v3.py`'s `calc_freq_sep()` |
| Occupied bandwidth (using Carson's Rule) | 9600 Hz | `rf_capstone_v3.py`'s `calc_bandwidth()` |
| Guard band | 4800 Hz | `rf_capstone_v3.py`'s `calc_freqs()` |
| Channel spacing (user-to-user) | 14400 Hz | `rf_capstone_v3.py`'s `calc_freqs()` |
| Coarse carrier frequency offset correction | `snr_threshold_db=20` | `gallant_input.synch.frequency_corrector.FrequencyCorrector`, implemented in `rf_capstone_v3.py`'s `receive_frames()` |
| Forward Error Correction | `FEC_REPEAT=3` repetition coding | `rxtx.frame_receiver.FrameReceiver` and `rxtx.utilities`'s `apply_fec_repetition()` / `decode_fec_repetition()` (see [§1.11](#111-error-control-checksum-and-optional-forward-error-correction)) |
| Byte order | Big Endian | design decision |
| Bit order | MSB first | design decision |

---

## 1.2 Two-User Frequency Plan

Each user is assigned a channel offset from a shared reference frequency
(`CENTER_FREQ`).  User 1's channel is shifted down and user 2 is shifted up.
The channels for both users are equally centered around a shared center frequency.
Each user's baseband tones are at +/-2400 Hz around their own center frequency:
-2400 Hz is "off" (`b'0'`), 2400 Hz is "on" (`b'1'`).   Each radio's transmit is tuned
to its own channel, while its receive is tuned to the other user's channel.

```
                                CENTER_FREQ (912.050 MHz)
                                     reference point only
                                    (never transmitted on)
                                           |
        <---------- 14.4 kHz ------------->|<---------- 14.4 kHz ------------->
        (channel_spacing)                  |         (channel_spacing)
        |                                  |                                  |
+---------------------------+              |              +---------------------------+
|      USER 1 CHANNEL       |              |              |      USER 2 CHANNEL       |
|     fc = 912.0356 MHz     |              |              |     fc = 912.0644 MHz     |
|                           |              |              |                           |
|   f0        fc       f1   |              |              |   f0        fc       f1   |
| -2.4kHz    (0)    +2.4kHz |              |              | -2.4kHz    (0)    +2.4kHz |
|   |---------|---------|   |              |              |   |---------|---------|   |
|<--- 9.6 kHz occupied BW ->|              |              |<--- 9.6 kHz occupied BW ->|
+---------------------------+              |              +---------------------------+
   User 1 TX  /  User 2 RX                                   User 2 TX  /  User 1 RX
```

* Occupied bandwidth per channel is computed via a form of Carson's Rule:
  `Bt = freq_sep + 2 * symbol_rate = 4800 Hz + 4800 Hz = 9600 Hz`.
* `channel_spacing = Bt + 2 * symbol_rate = 9600 Hz + 4800 Hz = 14400 Hz`, which leaves a
  4800 Hz guard band between the edge of one user's occupied bandwidth and the edge
  of the other user's occupied bandwidth.
* Both users share the same baseband tone plan (`f0 = -2400 Hz`, `f1 = +2400 Hz`
  relative to their own center).  Only their center frequency differs.

---

## 1.3 Transmit Chain

```
+-------------+     +----------------+     +-----------------------+     +--------------+     +------------------+     +-----------+
|   Message   | --> |  build_frame() | --> |    FSK2.modulate()    | --> |  apply_fir() | --> |   transmit()     | --> | USRP B200 |
| ASCII bytes |     |  Preamble +    |     |  bits -> continuous-  |     |  101-tap FIR |     |  UHD TX streamer,|     | DAC + RF  |
|             |     |  Syncword +    |     |  phase FSK IQ         |     |  low-pass    |     |  start/end-of-   |     | front end |
|             |     |  DataLen +     |     |  @ 240 kSa/s          |     |  (channel    |     |  burst           |     | -> antenna|
|             |     |  Data +        |     |  w/ Gaussian pulse    |     |  containment)|     |                  |     |           |
|             |     |  Checksum      |     |  shaping              |     |              |     |                  |     |           |
+-------------+     +----------------+     +-----------------------+     +--------------+     +------------------+     +-----------+
```

**Stage detail:**

1. **`build_frame()`** - assembles `PREAMBLE + SYNCWORD + DATA_LEN + DATA + CHECKSUM`
2. **`FSK2.modulate()`** - for each bit, selects `freq0` or `freq1` and generates
   `sps` (100) samples of a complex exponential at that instantaneous frequency,
   carrying the phase accumulator forward from symbol to symbol (`FSK2._update_phase()`).
   This produces continuous-phase FSK (CPFSK).  This stage also applies a Gaussian pulse
   shaping filter to smooth frequency transitions to reduce out-of-band spectral emmisions
   and side lobes.
3. **`apply_fir()`** - the same 101-tap low-pass FIR used on receive
   (`create_tailored_lpf()`) is applied to the modulated IQ before transmission, to keep
   this user's transmitted energy inside its 9600 Hz channel and out of the neighboring
   user's 9600 Hz channel.
4. **`transmit()`** - pushes the filtered IQ samples to the USRP's TX streamer as a
   single burst (`start_of_burst` / `end_of_burst` both set).

---

## 1.4 Receive Chain

```
+-----------+   +------------------+   +--------------+   +------------------+   +------------------------+   +----------------------+   +-------------------+   +-------------+
| USRP B200 |-->| UHD RX streamer  |-->|  apply_fir() |-->|  Frequency       |-->| demodulate_to_metric() |-->|  recover_clock_mm()  |-->|  FrameReceiver    |-->|   Message   |
| Antenna,  |   | recv() into a    |   |  101-tap FIR |   |  offset          |   |  FSK discriminator:    |   |  Mueller & Mueller   |   |  state machine:   |   |  (ASCII,    |
| ADC       |   | buffer,          |   |  low-pass    |   |  correction      |   |  differential phase    |   |  timing recovery,    |   |  syncword         |   |  printed to |
|           |   | accumulate       |   |  (channel    |   |                  |   |  between adjacent      |   |  interpolated x16,   |   |  correlation,     |   |  console)   |
|           |   | >= 1000 x sps    |   |  selection)  |   |                  |   |  samples               |   |  1 metric per        |   |  decode, and      |   |             |
|           |   | samples          |   |              |   |                  |   |                        |   |  symbol              |   |  frame parsing    |   |             |
+-----------+   +------------------+   +--------------+   +------------------+   +------------------------+   +----------------------+   +-------------------+   +-------------+
```

**Stage detail:**

1. **UHD RX streamer** - Continuously streams complex samples off the B200 into a
   growing buffer; processing is triggered once at least `1000 * sps` samples have
   accumulated.
2. **`apply_fir()`** - The shared channel low-pass filter (cutoff derived from the
   9600 Hz occupied bandwidth, rounded to the nearest 1 kHz and halved) rejects the
   neighboring user's channel and out-of-band noise before demodulation.
3. **Coarse Frequency Correction** - `receive_frames()` constructs the frequency
   offset corrector (see: `FrequencyCorrector()`) and processes chunks
   immediately after the channel LPF but before demodulation.  The frequency offset
   algorithm measures the samples provided, maintains a candidate buffer until a
   threshold is reached, and then locks in a frequency offset.
4. **`demodulate_to_metric()`** - a non-coherent FSK discriminator:
   Measures the instantaneous frequency of the signal.  No coherent carrier recovery
   is required.  Provides a continuous-valued symbol metric sampled at the input
   sample rate.
5. **`recover_clock_mm()`** - Mueller & Mueller (M&M) timing error detection, run
   over the discriminator output with 16x interpolation.  The implementation reduces the
   sample-rate metric stream down to exactly one representative metric per transmitted
   symbol without assuming the transmitter and receiver clocks are perfectly aligned.
6. **`FrameReceiver`** - a state machine that correlates on the syncword, then buffers
   up to the theoretical maximum frame length, and demodulates the frame as a whole.
   The demodulated binary data is parsed into fields and validated under its own
   strength.  The data field is FEC decoded before the checksum is verified.
   Frames with invalid data length values, and data that does not pass its
   integrity check are discarded.

---

## 1.5 Coarse Frequency Correction (CFC)

### The problem

The two-user channel plan in assumes each user's received signal shows up with its
tones sitting at exactly +/- 2400 Hz around baseband.  In practice, the two USRPs are two
independent, free-running local oscillators with no shared reference clock.  That drift
shows up at baseband as a carrier frequency offset (CFO).  Left uncorrected, a large
enough CFO could ruin symbol metrics and increase bit error rates (BER) and packet loss.

### Why coarse correction?

The CFO here is a static hardware offset.  The SDRs were not moving so there was no
need for continuous frequency correction.  However, dead air was skewing a very basic
frequency correction so I implemented a frequency correction sampler and lock.
Once the frequency corrector "locked in", it reduced processing cycles while
also correcting the frequency.  In practice, it was all that was needed.

### How `FrequencyCorrector` works

```
                     +-----------------------------------------------------+
                     |                  UNLOCKED (searching)               |
                     |                                                     |
  chunk of  -------->|  1. Welch PSD of chunk (freq-domain, averaged)      |
  IQ samples         |  2. Search +/-tolerance_hz around expected f0, f1   |
                     |  3. Keep peak only if SNR >= snr_threshold_db       |
                     |  4. Keep pair only if separation ~= freq_sep        |
                     |     (CFO-invariant check -- rejects false pairs)    |
                     |  5. Add candidate into buffer                       |
                     |  6. Look for lock_count candidates within           |
                     |     lock_std_hz of each other                       |
                     |         |                                           |
                     |         | cluster found                             |
                     |         v                                           |
                     |     LOCK: cfo_hz = median(cluster)                  |
                     +-----------------------------------------------------+
                                          |
                                          v
                     +-----------------------------------------------------+
                     |                   LOCKED (correcting)               |
                     |                                                     |
                     |  Apply phase-continuous digital downconversion:     |
                     |  No further measurement is attempted.               |
                     +-----------------------------------------------------+
```

* Detection (Welch PSD): Each unlocked chunk is analyzed with a Welch-averaged
  power spectral density.
* SNR gating: A candidate tone peak has to
  clear the noise floor by a real margin before it's trusted.  This was important
  to reject spectral noise in the search window.
* CFO-invariant false-pair rejection (`sep_tolerance_hz`, default 100 Hz): the two
  accepted peaks must be separated by close to the `freq_sep`.  Another important
  discriminator to help ignore noise.
* Cluster-based locking: Candidate values are accumulated in a buffer and the
  corrector only locks once it finds a sufficient number of candidates.
* Correction (phase-continuous NCO mixing): once locked, every subsequent chunk is
  corrected with the phase accumulator persisting across chunk boundaries.  After
  locking, no further measurement is made, keeping the steady-state processing
  cost low.

---

## 1.6 Frame Format

```
|<---------------------------- HEADER (104 bits) ----------------------------->|<---------------- PAYLOAD (variable) ----------------->|
+---------------------------+-----------------------------+--------------------+------------------------------+------------------------+
|     PREAMBLE (64 bits)    |      SYNCWORD (32 bits)     |  DATA_LEN (8 bit)  |        DATA (8 x N bits)      |   CHECKSUM (8 bit)    |
|  10 ... (32x)             |      0xD8DC512E             |  unsigned int N    |     payload bytes, MSB-first, |  sum(FEC-decoded      |
|                           |      1101 1000 1101 1100    |  (DATA field len   |     big-endian, FEC-encoded   |      DATA bytes)      |
|                           |      0101 0001 0010 1110    |   in bytes)        |                               |  & 0xFF               |
+---------------------------+-----------------------------+--------------------+-------------------------------+-----------------------+
   bit sync                    frame delimiter,              tells the           the actual message               error
   (alternating pattern)       located via correlation        receiver how       (e.g. ASCII text)                detection
                                against a bipolar              many DATA                                          only
                                reference)                     bytes follow
```

* Byte order: Big Endian.
* Bit order: MSB first.
* PREAMBLE - 64 bits of alternating `10` (`PREAMBLE = 32 * b'10'`), still built
  into every transmitted frame by `build_frame()`.  **Confirmed:** the live
  `receive_frames()` no longer converts `PREAMBLE` into a correlation array or passes
  it to `FrameReceiver` at all - the constructor call is
  `FrameReceiver(modem=modem, syncword=syncword, checksum=generate_checksum,
  fec_repeat=fec_repeat, max_data_bytes=max_data_bytes, debug=debug)`, with no
  preamble argument.  Frame acquisition is anchored entirely on syncword correlation
  (§1.10).  The preamble is transmitted but, as far as I can tell from the live wiring,
  currently unused on receive - its only remaining plausible value is AGC/bit-sync
  settling time ahead of the syncword, and even that isn't something the receive code
  visibly depends on today.
* SYNCWORD - 32-bit fixed pattern `0xD8DC512E`
  (`1101 1000 1101 1100 0101 0001 0010 1110`).  Chosen as a fixed, low-autocorrelation
  bit pattern.  In the receiver this pattern does double duty: `find_frame_start()`
  correlates against it directly to acquire the frame, and then an exact
  bit-string comparison against the fully-decoded syncword confirms alignment before
  anything else is trusted.  The specific syncword was chosen for its binary balance
  (equal number of 1s and 0s), its high transition count (1->0 and 0->1 transitions),
  and low repeats (short runs of symbols were scored higher).
* DATA_LEN - 8-bit unsigned integer, the number of bytes (not bits) in the
  `DATA` field that follows.  FEC repetition to the message before computing `DATA_LEN`.
* DATA - The payload itself.  Every transmitted `DATA` field is 3x repetition-coded by
  default, not merely capable of it.  The checksum is generated from the original binary
  instead of the FEC-coded binary.
* CHECKSUM - 8-bit additive checksum of the post-FEC-decoded `DATA` field
  computed identically on the transmitter and receiver.

---

## 1.7 Modulation & Pulse-Shaping Design Rationale

**Choice: Gaussian-filtered, continuous-phase 2-FSK (GFSK).**

* Why FSK?: FSK's demodulation is non-coherently which removes the need for
  carrier phase recovery, simplifying the implementation.
* Why continuous phase (CPFSK)?:
  `FSK2.modulate()` carries the phase accumulator across symbol boundaries instead
  of resetting phase to 0 at every new symbol.  An abrupt phase reset at every
  symbol edge would inject sharp discontinuities into the waveform.  Continuous phase
  keeps the transmitted spectrum close to the theoretical 9600 Hz occupied bandwidth
  this protocol's channel plan is built around.
* Pulse shaping: Gaussian pre-modulation filtering (GFSK).
  A Gaussian filter applied to the bit stream before frequency modulation.  This
  was chosen to round off the sharp rectangular symbol transitions and further
  suppress out-of-band spectral energy beyond what continuous phase alone provides.

---

## 1.8 Demodulation & Symbol-Decision Design Rationale

* `demodulate_to_metric()` computes the instantaneous frequency by measuring the
  sample-to-sample phase change.  For BFSK this metric clusters around two values,
  one per tone.  This discriminator is non-coherent, because it doesn't need an
  absolute carrier phase reference, and only requires the tones are far enough
  apart to be distinguished from each other.
* `decide_symbols()` - The initial K-Means implementation was making skewed
  measurements over partial decodes.  I added a threshold-based override to allow
  the caller to bypass KMeans clustering by using a threshold instead.  While the
  class supports an adaptive threshold, this was bypassed because of trailing noise
  on the frame being decoded.  Confidence is high that the current threshold value
  is sufficient given the frequency offset correction that is happening before
  `FrameReceiver()` is called to process samples.

---

## 1.9 Clock Recovery Design Rationale

Mueller & Muller (M&M) timing error detector

* `FSK2` ships a naive `recover_symbols()` that just samples the discriminator output
  at fixed `sps`-spaced intervals.  This is only correct if the transmitter and
  receiver sample clocks are perfectly aligned with no drift, which is not a safe
  assumption across two independent SDRs.
* In the live RX path that method is bypassed in lieu of `recover_clock_mm()`,
  a Mueller & Muller discrete-time timing-error-tracking synchronizer.  M&M looks at
  the discriminator output stream and adaptively locates the optimal sampling instant
  for each symbol.  It corrects for clock rate mismatches between the two radios as the
  frame is received.
* `interp=16` interpolates the metric stream 16x internally before the M&M loop
  searches for the symbol boundary.  This improves timing-instant resolution with
  a finer boundary estimate.
* The receiver does not require a shared reference clock or pre-arranged timing
  between the two SDRs because it recovers symbol timing directly from the received
  signal itself, per frame.

---

## 1.10 Frame State Machine

`rxtx.frame_receiver.FrameReceiver` is a state machine that consumes a continuous
stream of clock-recovered, per-symbol metrics and returns complete, checksum-validated
payloads.

```
                     buffer too small, or syncword correlation
                     found no match yet (keeps a fixed window of SYNCWORD_BITS - 1
                     in case the syncword straddles a chunk
                     boundary; wait for more incoming samples)
                  +-------------------------------------------+
                  |                                             |
                  v                                             |
           +--------------+                                     |
     +---->|  SEARCHING   |-------------------------------------+
     |     +--------------+
     |            |
     |            | syncword-shaped correlation hit
     |            | (find_frame_start(), threshold=0.65)
     |            | -- discard everything before it
     |            v
     |     +--------------------------------------------------------+
     |     |                     FULL_DECODE                        |
     |     |  buffered symbols >= maximum_bits?                     |<--+
     |     |                                                        |   | no:
     |     |                                                        |---+  wait for
     |     |                                                        |     more samples
     |     |  yes: decide_symbols() for the whole frame             |
     |     |                                                        |
     |     +--------------------------------------------------------+
     |            |
     |            v
     |     +----------------------------+
     |     | (a) decoded bits == the    |   mismatch: drop 1 symbol,
     |     |     EXACT expected         |-------------------------------+
     |     |     syncword bit-string?   |                               |
     |     +----------------------------+                               |
     |            | exact match                                         |
     |            v                                                     |
     |     +----------------------------+                               |
     |     | (b) 0 < DATA_LEN <=        |   out of range: drop 1        |
     |     |     max_data_bytes?        |    symbol                     |
     |     +----------------------------+-------------------------------+
     |            | valid                                               |
     |            v                                                     |
     |     +----------------------------+                               |
     |     | (c) decode_fec_repetition  |   checksum mismatch: drop     |
     |     |     then verify the        |    the frame                  |
     |     |     checksum matches?      |-------------------------------+
     |     +----------------------------+                               |
     |            | match -- frame emitted!                             |
     |            v                                                     v
     +----[ state -> SEARCHING, ready for the next frame ]<-------------+
```

* SEARCHING (`_find_frame()`) - Correlates against the bipolar syncword.  On a hit,
  everything before the match is discarded and the machine advances straight to
  `FULL_DECODE`.  If nothing clears the correlation threshold, the last
  `SYNCWORD_BITS - 1` symbols are retained (in case the real syncword straddles
  the boundary between this chunk and the next) and the machine waits for more data.
* FULL_DECODE (`_full_decode()`) - Verifies enough bits are in the buffer to hold
  an entire frame by testing the buffer length against the maximum length of a frame.
  If the buffer is long enough to hold and entire frame, the final demodulation stage
  is executed and the buffer is decoded to binary.  Then the frame is checked for
  validity and integrity.
  1. **Syncword** - An exact bit-string comparison against the known syncword is
     performed.  A mismatch here means the correlation hit was a false positive and
     the machine returns to `SEARCHING` after dropping a single symbol (just in case
     an actual syncword is straddling the boundary between process samples).
  2. **`DATA_LEN`** - This value is validated against the maximum DATA field length
     the protocol was designed to handle.  An out-of-range value is treated the same
     as a bad syncword: one symbol is dropped and the machine goes back to `SEARCHING`.
  3. **`DATA` + checksum** Slices out the DATA bits, retrieves the the trailing
     `CHECKSUM_BITS`), runs `decode_fec_repetition()` on the `DATA` field, then
     computes and compares the checksum.  A match emits the frame and the machine resets
     to `SEARCHING`.  A mismatch drops the frame and also resets to `SEARCHING`.

---

## 1.11 Error Control: Checksum, and Forward Error Correction

* Checksum (detection): An 8-bit additive checksum computed over the `DATA` field on
  transmit and re-computed identically on receive.  If the two don't match then the
  `FrameReceiver` drops the frame and returns to `SEARCHING`.
* Forward Error Correction (FEC) - Helps the protocol easily survive occasional bit
  flips in the data by using a "majority vote" decoding algorithm.

---

## 1.12 Future Work: Given another week, what is next?

### Magic Numbers

There are a shameful number of hard-coded values sprinkled throughout my implementation.
Some of the hard-coded values would break the implementation if certain constants
ever changed.

* `receive_frames()` utilizes an arbitrary, hard-coded multiple of the sps as a
  threshold to process received samples.  The actual value should be tied to the
  protocol.
* The transmit gain is hard-coded and should be automated.
* The receive gain is hard-coded and should be automated.
* The Gaussian bandwidth-time product is hard-coded and should be replaced with a
  dynamic bandwidth-time optimization subsystem.
* The syncword correlation threshold was manually tuned to the current environment.
  Instead, it should be replaced with an algorithm to update the threshold based on
  the SNR or the Received Signal Strength Indicator (RSSI).

### Improve Effeciency

* The sample rate value could be better optimized for the protocol.
* The effective samples-per-symbol are too high to be efficient.
* Earlier correlation of a continuos valued bipolar, or even complex-valued, syncword
  could possibly reduce the amount of work FrameReceiver has to do to process samples.

### Lower Packet Loss

* Better checksum: swap the additive checksum for CRC-8 or CRC-16.
* Implement a block code to replace the FEC repeats.
* Sustained usage could change the frequency offset which may necessitate an adaptive
  frequency offset correction.  Even a minor refactor to include a `reset()` feature
  in the current version could aid in adapting to further frequency offsets.
* In the `--debug` output, the dropped frames almost *always* appear to be because
  the receiver missed a syncword.  The "exact" check for the syncword might not
  be necessary.  I see very low, but non-zero, syncword BERs on dropped packets.
  It might be enough to rely on the syncword correlation, skip the *exact* syncword
  check, and have more faith in the correlation, FEC-encoding, and checksum.

### Variable Center Frequency

The center of the guard band is hard-coded.  I left some commented code in the
arg parse functionality to allow the user to choose a different center frequency.
However, this feature/refactor would require significant safety guards.

### Improved Interfaced

* The text user interface (TUI) leaves a lot to be desired.  An actual chat program
  would have separate windows for send and receive.  The BER/packet-loss calculation
  method, currently implemented, requires redirecting output to files to be parsed
  later by `rf_capstone_calc_error_rate.py`.
* The received data "steps on" the user prompt for input.
  In non-`--interact` mode, everything works fine.  However, `--interact` mode,
  `--debug` or not, requires significant improvement.
* User input, taken in `--interact`, non-`--debug`, mode is truncated at the maximum
  length of the `DATA` field (not counting FEC-encoding).  Instead of being ignored,
  discrete messages should be formed, and transmitted, from longer messages.

---

# PART 2: OPERATIONAL DOCUMENTATION

## 2.1 Prerequisites

**Hardware**
- 2x Ettus Research USRP B200-series SDR (tested: B206mini, B205mini)
- 2x USB 3.0 connection to the host machine(s) (same machine, two SDRs is the
  documented/tested configuration)
- 2x antennas appropriate for the 902–928 MHz ISM band (this protocol operates around
  912 MHz)

**Software**
- Linux (UHD/USRP tooling is best supported here; this guide assumes Ubuntu/Debian)
- Python 3.10+
- Ettus UHD driver + firmware/FPGA images
- Python packages (see: `gallant_input/requirements.txt`)

## 2.2 Setup

### Step 1 - Install the UHD driver (system-level)

```bash
sudo apt update
sudo apt install -y libuhd-dev uhd-host python3-uhd

# Download the FPGA/firmware images UHD needs to talk to the B200/B205/B206
sudo uhd_images_downloader
```

### Step 2 - Verify your SDRs are visible to the host

```bash
uhd_find_devices
```

You should see one entry per connected USRP, each with a `serial` field.
Write these two serial numbers down as you need them later.

```
--------------------------------------------------
-- UHD Device 0
--------------------------------------------------
Device Address:
    serial: 317650F
    product: B205mini
    type: b200
--------------------------------------------------
-- UHD Device 1
--------------------------------------------------
Device Address:
    serial: 3512A99
    product: B206mini
    type: b200
```

### Step 3 - Access the repository

Enter the Gallant Input (GAIN) repository

#### If available locally

```bash
cd ./code/python/
ls -l  # Verify the gallant_input package is present
```

### Step 4 - Create a virtual environment and install Python dependencies

A ready-to-run setup script is provided: `setup_env.sh`.
However, it is not particularly robust.

```bash
python3 -m venv .venv      # Optional?
source .venv/bin/activate  # Optional?

pip install --upgrade pip
pip install -r gallant_input/requirements.txt

# The `uhd` Python package is normally provided by the system package
# `python3-uhd` installed in Step 1. If your venv can't `import uhd`,
# either create the venv with --system-site-packages, or install UHD's
# Python bindings into the venv per Ettus's UHD Python API instructions.

# Install this repo's own packages (gallant_input, rxtx) so
# `rf_capstone_v3.py`'s imports resolve.
# >>> CONFIRM against your actual repo layout - use whichever of these
#     matches what's actually in the repo root:
pip install -e .
#   -- or, if there's no setup.py/pyproject.toml --
# export PYTHONPATH="$PWD:$PYTHONPATH"
```

### Step 5 - Sanity-check the install

```bash
python3 -c "import uhd, numpy, scipy, matplotlib, sklearn, sigmf; print('OK')"
python3 -c "from gallant_input.modem.fsk2 import FSK2; print('OK')"
```

Both should print `OK` with no import errors before you proceed.

## 2.3 Running the Protocol (Two Users, One Machine, Two SDRs)

### One machine, two SDRs

Successful execution of `rf_capstone_v3.py`:
* May require each side of the link to be told which physical SDR to use (`--serial`)
* Requires a user number (`--user 1` or `--user 2`).
* User 1 and User 2 must be run in separate terminals

```bash
# One-time, each terminal:
cd gallant-input && source .venv/bin/activate
```

**Terminal 1:**
```bash
python rf_capstone_v3.py --serial 317650F --user 1
```

**Terminal 2:**
```bash
python rf_capstone_v3.py --serial 3512A99 --user 2
```

### Two machines, one SDR each

Each machine requires a different user number.

**Machine 1:**
```bash
python rf_capstone_v3.py --user 1
```

**Machine 2:**
```bash
python rf_capstone_v3.py --user 2
```

### Commonality

Each side will print incoming messages as they're received:

```
[RX] Received: This is my test input.
```

Stop either side with `Ctrl+C` (which gracefully signals the receive thread to stop and
joins it before exiting).

### Command-line options

```bash
python rf_capstone_v3.py --help  # For details
```

| Flag | Required | Description |
|---|---|---|
| `-u`, `--user` | Yes | Which user this process is: `1` or `2`. |
| `-s`, `--serial` | No | Serial number of the USRP to bind to (from `uhd_find_devices`).  If omitted, connects to any device matching `type=b200`. |
| `-d`, `--debug` | No | Enables verbose logging, fixes the transmitted message to a known test string, and prints live Bit Error Rate (BER) for the syncword and data fields - see §2.4. |
| `-i`, `--interact` | No | Lets you control what/when is transmitted instead of the default automatic behavior.  Combined with `--debug`, prompts with `Press <ENTER> to transmit...` before each send instead of transmitting on a forced half-duplex timing schedule.  Without `--debug`, prompts `Enter a message to transmit:` for a free-text message instead of picking randomly from the built-in message list. |

## 2.4 Debug Mode: Measuring Bit Error Rate / Packet Loss

For characterizing link quality (same machine, two SDRs), run both sides with
`--debug`, redirecting output to files so you can inspect it afterward:

```bash
export TMP_OUTPUT=/tmp
export USER1_OUTPUT=$TMP_OUTPUT/rf_capstone_user1.out
export USER2_OUTPUT=$TMP_OUTPUT/rf_capstone_user2.out
```

**Terminal 1:**
```bash
python -u rf_capstone_v3.py --serial 317650F --user 1 --debug > "$USER1_OUTPUT" 2>&1
```

**Terminal 2:**
```bash
python -u rf_capstone_v3.py --serial 3512A99 --user 2 --debug > "$USER2_OUTPUT" 2>&1
```

Let it run, then `Ctrl+C` both sides.  Each output file will contain per-frame
`[RX] SYNCWORD BER: ...` and `[RX] DATA BER: ...` lines you can grep/aggregate to
compute overall error rates and packet loss for that run (packets whose checksum
failed are logged as `[RX] Dropping failed checksum` and never reach the BER-compared
data line).

A script has been provided to automate the process (assuming the correct environment
variables have been set).

```bash
python rf_capstone_calc_error_rate.py
```

## 2.5 Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `RuntimeError: No devices found for ...` | The specified `--serial` isn't connected, or no B200-type device is attached at all.  Run `uhd_find_devices` to confirm what's actually visible, and double check the USB 3.0 cable/port. |
| `ImportError: No module named 'uhd'` | UHD's Python bindings aren't visible to your interpreter/venv.  Re-check Step 1/Step 4 above - either install `python3-uhd` system-wide and create your venv with `--system-site-packages`, or install UHD's Python API into the venv directly. |
| No messages received on either side | Confirm both processes are actually using different `--user` values (`1` and `2`) - two processes with the same `--user` value will compute the *same* channel and talk over each other instead of to each other.  Also confirm antennas are attached and within range of each other. |
| Received messages look garbled / frequent `Dropping failed checksum` | Check RX/TX gain (`rx_gain`/`tx_gain`, currently hard-coded to `40` dB in `main()`) - too low a gain starves the discriminator of SNR; too high can saturate the front end.  Also confirm nothing else is transmitting in the 912 MHz ISM band nearby.  If this persists specifically at the *start* of a run and then clears up, that's consistent with the coarse frequency corrector still locking - it needs a run of confident measurements before it starts correcting, so give it a few seconds. |
| `ValueError: RX Gain ... out of safe range` / `TX Gain ... out of safe range` | The requested gain exceeds what your specific B200-series unit supports (B205mini/B206mini gain ranges can differ slightly by unit).  Lower the hard-coded `rx_gain`/`tx_gain` values to fit your hardware's reported range. |

---

## Appendix A: `setup_env.sh`

A copy of this script is included alongside this document
(`setup_env.sh`).  It automates some of the steps referenced above.  However,
it is not foolproof.  Review it before running as it installs system packages
with `sudo` and assumes Ubuntu/Debian `apt`.

```bash
#!/usr/bin/env bash
# See setup_env.sh (included alongside this document) for the runnable version.
```
