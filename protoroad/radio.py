"""Common-use functionality for SDRs."""

# Standard Imports
from typing import Final
# Third Party Imports
import numpy as np
import uhd  # pylint: disable=import-error
# Local Imports

DEFAULT_CHANNEL: Final[int] = 0      # Single-channel B206mini
DEFAULT_MCR: Final[float] = 32e6     # Master clock rate; 32 MHz / 1 Msps = 32
DEFAULT_TAIL_PAD: Final[int] = 256   # Zero samples appended to every TX burst
RATE_TOLERANCE: Final[float] = 1.0   # Max |requested - actual| sample rate (S/s)
RX_ANTENNA: Final[str] = "RX2"       # Receive port
TX_ANTENNA: Final[str] = "TX/RX"     # Transmit port
TX_SEND_TIMEOUT: Final[float] = 1.0  # Seconds to wait on streamer.send()


class Radio:
    """Own one USRP and its streamers for the life of the program."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, samp_rate: float | int, center_freq: float | int, rx_gain: float | int,
                 tx_gain: float | int, serial: str | None = None, lo_offset: float | int = 0,
                 master_clock_rate: float = DEFAULT_MCR, channel: int = DEFAULT_CHANNEL):
        """Class ctor.

        Args:
            samp_rate: Sample rate (S/s), RX and TX.
            center_freq: Center frequency (Hz), RX and TX.
            rx_gain: Receive gain (dB).
            tx_gain: Transmit gain (dB).
            serial: [OPTIONAL] Serial number of the USRP to use; None uses the first B2xx found.
            lo_offset: [OPTIONAL] Analog LO offset (Hz); moves the DC spike out of band.
            master_clock_rate: [OPTIONAL] FPGA master clock rate (Hz).
            channel: [OPTIONAL] Channel.
        """
        # LOCAL VARIABLES
        self._channel = channel                     # Channel used for RX and TX
        self._usrp = _build_usrp(serial=serial, master_clock_rate=master_clock_rate)
        self._tx_streamer = None                    # Created once, below
        self._rx_streamer = None                    # Created once, below
        self._tx_max_samps = 0                      # Largest buffer one send() accepts

        # CONFIGURE IT
        _configure_usrp_rx(self._usrp, samp_rate, center_freq, rx_gain, lo_offset, channel)
        _configure_usrp_tx(self._usrp, samp_rate, center_freq, tx_gain, lo_offset, channel)

        # STREAMERS (once, for the life of the object)
        self._tx_streamer = self._usrp.get_tx_stream(self._build_stream_args())
        self._rx_streamer = self._usrp.get_rx_stream(self._build_stream_args())
        self._tx_max_samps = self._tx_streamer.get_max_num_samps()
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    @property
    def usrp(self) -> uhd.usrp.MultiUSRP:
        """Escape hatch to the underlying MultiUSRP (debugging, sensors, etc.)."""
        return self._usrp

    def transmit(self, samples: np.ndarray, tail_pad: int = DEFAULT_TAIL_PAD) -> int:
        """Transmit an array of samples as one burst.

        Args:
            samples: Complex baseband samples (already pulse shaped and scaled).
            tail_pad: [OPTIONAL] Number of zero samples appended so the RRC tail isn't truncated.

        Returns:
            Number of samples sent, including the tail padding.
        """
        # LOCAL VARIABLES
        burst = None                         # Samples + zero padding, as complex64
        metadata = uhd.types.TXMetadata()    # Start/end of burst flags
        sent = 0                             # Total samples sent

        # INPUT VALIDATION
        if samples.ndim != 1 or len(samples) == 0:
            raise ValueError(f"Expected a non-empty 1-D array, got shape {samples.shape}")

        # SEND IT
        burst = np.concatenate([np.asarray(samples, dtype=np.complex64),
                                np.zeros(tail_pad, dtype=np.complex64)])
        metadata.start_of_burst = True
        metadata.end_of_burst = False
        # A single send() is capped at max_num_samps, so loop over chunks of the burst
        while sent < len(burst):
            chunk = burst[sent:sent + self._tx_max_samps]
            metadata.end_of_burst = sent + len(chunk) >= len(burst)
            num = self._tx_streamer.send(chunk, metadata, TX_SEND_TIMEOUT)
            if num == 0:
                raise RuntimeError(f"TX send timed out after {sent}-of-{len(burst)} samples")
            sent += num
            metadata.start_of_burst = False

        # DONE
        return sent

    def _build_stream_args(self) -> uhd.usrp.StreamArgs:
        """Host format complex float32, over-the-wire format complex int16."""
        stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
        stream_args.channels = [self._channel]
        return stream_args


def _build_usrp(serial: str | None, master_clock_rate: float) -> uhd.usrp.MultiUSRP:
    """Build the USRP object."""
    dev_args = f"type=b200,master_clock_rate={master_clock_rate}"
    if serial:
        dev_args += f",serial={serial}"
    return uhd.usrp.MultiUSRP(dev_args)


# pylint: disable=too-many-arguments,too-many-positional-arguments
def _configure_usrp_rx(usrp: uhd.usrp.MultiUSRP, samp_rate: float | int,
                       center_freq: float | int, gain: float | int, lo_offset: float | int,
                       channel: int) -> None:
    """Configure a USRP SDR's receive chain using the provided values."""
    _validate_gain(gain_range=usrp.get_rx_gain_range(channel), gain_value=gain, label="RX")
    usrp.set_rx_rate(float(samp_rate), channel)
    _validate_rate(actual=usrp.get_rx_rate(channel), requested=samp_rate, label="RX")
    usrp.set_rx_freq(uhd.types.TuneRequest(float(center_freq), float(lo_offset)), channel)
    usrp.set_rx_gain(float(gain), channel)
    usrp.set_rx_antenna(RX_ANTENNA, channel)


def _configure_usrp_tx(usrp: uhd.usrp.MultiUSRP, samp_rate: float | int,
                       center_freq: float | int, gain: float | int, lo_offset: float | int,
                       channel: int) -> None:
    """Configure a USRP SDR's transmit chain using the provided values."""
    _validate_gain(gain_range=usrp.get_tx_gain_range(channel), gain_value=gain, label="TX")
    usrp.set_tx_rate(float(samp_rate), channel)
    _validate_rate(actual=usrp.get_tx_rate(channel), requested=samp_rate, label="TX")
    usrp.set_tx_freq(uhd.types.TuneRequest(float(center_freq), float(lo_offset)), channel)
    usrp.set_tx_gain(float(gain), channel)
    usrp.set_tx_antenna(TX_ANTENNA, channel)
# pylint: enable=too-many-arguments,too-many-positional-arguments


def _validate_gain(gain_range: uhd.types.MetaRange, gain_value: float | int, label: str) -> None:
    """Validate a gain value against the hardware's reported range."""
    min_gain = gain_range.start()  # 0.0 on B2xx
    max_gain = gain_range.stop()   # ~76 dB RX, ~89.8 dB TX on B2xx
    if not min_gain <= gain_value <= max_gain:
        raise ValueError(f"{label} gain {gain_value} dB out of range: [{min_gain}, {max_gain}]")


def _validate_rate(actual: float, requested: float | int, label: str) -> None:
    """UHD silently coerces unsupported rates; fail loudly instead."""
    if abs(actual - requested) > RATE_TOLERANCE:
        raise RuntimeError(f"{label} rate: requested {requested} S/s, hardware gave {actual} S/s")
