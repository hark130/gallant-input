"""Common-use functionality for SDRs."""

# Standard Imports
import threading
# Third Party Imports
import numpy as np
import uhd  # pylint: disable=import-error
# Local Imports


def build_usrp(serial: str) -> uhd.usrp.MultiUSRP:
    """Build the USRP object."""
    if serial:
        usrp = uhd.usrp.MultiUSRP('serial=' + serial)
    else:
        usrp = uhd.usrp.MultiUSRP("type=b200")
    return usrp


# pylint: disable=too-many-arguments,too-many-positional-arguments
def configure_usrp(usrp: uhd.usrp.multi_usrp.MultiUSRP, samp_rate: float | int,
                   center_freq: float | int, gain: float | int, channel: int = 0) -> None:
    """Configure a USRP SDR using the provided values.

    Args:
        usrp: uhd.usrp object to configure.
        samp_rate: Sample rate.
        center_freq: Center frequency.
        gain: Gain.
        channel: [OPTIONAL] Channel.
    """
    # INPUT VALIDATION
    # CFT!?!

    # CONFIGURE IT
    _configure_usrp_rx(usrp, samp_rate, center_freq, gain, channel)
    _configure_usrp_tx(usrp, samp_rate, center_freq, gain, channel)
# pylint: enable=too-many-arguments,too-many-positional-arguments


def transmit(usrp: uhd.usrp.multi_usrp.MultiUSRP, samples: np.ndarray) -> int:
    """Transmit an array of samples."""
    stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
    stream_args.channels = [0]
    streamer = usrp.get_tx_stream(stream_args)
    metadata = uhd.types.TXMetadata()
    metadata.start_of_burst = True
    metadata.end_of_burst = True
    samples = np.asarray(samples, dtype=np.complex64)
    sent = streamer.send(samples, metadata)

    # DONE
    return sent


def _configure_usrp_rx(usrp: uhd.usrp.multi_usrp.MultiUSRP, samp_rate: float | int,
                       center_freq: float | int, gain: float | int, channel: int) -> None:
    """Configure a USRP SDR's receive antenna using the provided values."""
    _validate_usrp_rx_gain(usrp=usrp, gain_value=gain, channel=channel)
    tune_request = uhd.types.TuneRequest(center_freq)
    usrp.set_rx_rate(samp_rate)
    usrp.set_rx_freq(tune_request)
    usrp.set_rx_gain(gain)
    usrp.set_rx_antenna("RX2", channel)


def _configure_usrp_tx(usrp: uhd.usrp.multi_usrp.MultiUSRP, samp_rate: float | int,
                       center_freq: float | int, gain: float | int, channel: int) -> None:
    """Configure a USRP SDR's transmit antenna using the provided values."""
    _validate_usrp_tx_gain(usrp=usrp, gain_value=gain, channel=channel)
    tune_request = uhd.types.TuneRequest(center_freq)
    usrp.set_tx_rate(samp_rate)
    usrp.set_tx_freq(tune_request)
    usrp.set_tx_gain(gain)
    tx_ant = usrp.get_tx_antennas(channel)
    usrp.set_tx_antenna(tx_ant[0], channel)  # TRX


def _validate_usrp_rx_gain(usrp: uhd.usrp.multi_usrp.MultiUSRP, gain_value: float | int,
                           channel: int) -> None:
    """Validate a USRP RX gain value against the hardware."""
    gain_range = usrp.get_rx_gain_range(channel)
    # Extract min, max, and step boundaries from the UHD range object
    min_gain = gain_range.start()  # Will return 0.0
    max_gain = gain_range.stop()   # Will return 76.0 for RX, 89.8 for TX
    if not min_gain <= gain_value <= max_gain:
        raise ValueError(f'RX Gain {gain_value} db out of safe range: [{min_gain}, {max_gain}]')


def _validate_usrp_tx_gain(usrp: uhd.usrp.multi_usrp.MultiUSRP, gain_value: float | int,
                           channel: int) -> None:
    """Validate a USRP RX gain value against the hardware."""
    gain_range = usrp.get_tx_gain_range(channel)
    # Extract min, max, and step boundaries from the UHD range object
    min_gain = gain_range.start()  # Will return 0.0
    max_gain = gain_range.stop()   # Will return 89.8 for TX
    if not min_gain <= gain_value <= max_gain:
        raise ValueError(f'TX Gain {gain_value} db out of safe range: [{min_gain}, {max_gain}]')
