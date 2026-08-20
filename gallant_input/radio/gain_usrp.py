"""Common-use functionality for USRP SDRs."""

# Standard Imports
# Third Party Imports
import numpy
import uhd
# Local Imports
from gallant_input.radio.config_direction import ConfigDirection
from gallant_input.validation import validate_pos_float_or_int, validate_int, validate_type


def configure_usrp(usrp: uhd.usrp.multi_usrp.MultiUSRP, samp_rate: float | int,
                   center_freq: float | int, gain: float | int, channel: int = 0,
                   direction: ConfigDirection = ConfigDirection.BOTH) -> None:
    """Configure a USRP SDR using the provided values.

    Args:
        usrp: uhd.usrp object to configure.
        samp_rate: Sample rate.
        center_freq: Center frequency.
        gain: Gain.
        channel: [OPTIONAL] Channel.
        direction: [OPTIONAL] The direction to configure.
            (see: radio.config_direction.ConfigDirection)
    """
    # INPUT VALIDATION
    _validate_usrp_object(usrp, 'usrp')
    validate_pos_float_or_int(samp_rate, 'samp_rate')
    validate_pos_float_or_int(center_freq, 'center_freq')
    # The gain argument is validated by lower level function calls
    validate_int(channel, 'channel')

    # CONFIGURE IT
    if direction == ConfigDirection.RX:
        _configure_usrp_rx(usrp, samp_rate, center_freq, gain, channel)
    elif direction == ConfigDirection.TX:
        _configure_usrp_tx(usrp, samp_rate, center_freq, gain, channel)
    elif direction == ConfigDirection.BOTH:
        _configure_usrp_rx(usrp, samp_rate, center_freq, gain, channel)
        _configure_usrp_tx(usrp, samp_rate, center_freq, gain, channel)


def receive(usrp: uhd.usrp.multi_usrp.MultiUSRP, stop_event: threading.Event):
    """Capture an infinite number of samples (until stop_event triggers)."""
    stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
    stream_args.channels = [0]
    streamer = usrp.get_rx_stream(stream_args)
    buffer = numpy.empty((1, streamer.get_max_num_samps()), dtype=numpy.complex64)
    metadata = uhd.types.RXMetadata()
    received = numpy.empty(0, dtype=numpy.complex64)
    total = 0

    # Start continuous RX.
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    try:
        while not stop_event.is_set():
            count = streamer.recv(buffer, metadata)
            if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                raise RuntimeError(f"RX error: {metadata.strerror()}")
            received = numpy.concatenate([received, buffer[0, :count]])
    finally:
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        streamer.issue_stream_cmd(stream_cmd)

    # DONE
    return received


def receive_num(usrp: uhd.usrp.multi_usrp.MultiUSRP, num_samples: int):
    """Capture a finite number of samples."""
    stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
    stream_args.channels = [0]
    streamer = usrp.get_rx_stream(stream_args)
    buffer = numpy.empty((1, streamer.get_max_num_samps()), dtype=numpy.complex64)
    metadata = uhd.types.RXMetadata()
    received = numpy.empty(num_samples, dtype=numpy.complex64)
    total = 0

    # Start continuous RX.
    stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.start_cont)
    stream_cmd.stream_now = True
    streamer.issue_stream_cmd(stream_cmd)

    try:
        while total < num_samples:
            count = streamer.recv(buffer, metadata)
            if metadata.error_code != uhd.types.RXMetadataErrorCode.none:
                raise RuntimeError(f"RX error: {metadata.strerror()}")
            count = min(count, num_samples - total)
            received[total:total + count] = buffer[0, :count]
            total += count
    finally:
        stream_cmd = uhd.types.StreamCMD(uhd.types.StreamMode.stop_cont)
        streamer.issue_stream_cmd(stream_cmd)

    # DONE
    return received


def transmit(usrp: uhd.usrp.multi_usrp.MultiUSRP, samples: numpy.ndarray) -> int:
    stream_args = uhd.usrp.StreamArgs("fc32", "sc16")
    stream_args.channels = [0]
    streamer = usrp.get_tx_stream(stream_args)
    metadata = uhd.types.TXMetadata()
    metadata.start_of_burst = True
    metadata.end_of_burst = True
    samples = numpy.asarray(samples, dtype=numpy.complex64)
    sent = streamer.send(samples, metadata)

    # DONE
    return sent


def _configure_usrp_rx(usrp: uhd.usrp.multi_usrp.MultiUSRP, samp_rate: float | int,
                       center_freq: float | int, gain: float | int, channel: int) -> None:
    """Configure a USRP SDR's receive antenna using the provided values.

    Only validates the gain value: type, value, and against the hardware's channel.
    """
    # INPUT VALIDATION
    _validate_usrp_rx_gain(usrp=usrp, gain_value=gain, channel=channel)
    # CONFIGURE IT
    usrp.set_rx_rate(samp_rate)
    usrp.set_rx_freq(center_freq)
    usrp.set_rx_gain(gain)
    usrp.set_rx_antenna("RX2", channel)


def _configure_usrp_tx(usrp: uhd.usrp.multi_usrp.MultiUSRP, samp_rate: float | int,
                       center_freq: float | int, gain: float | int, channel: int) -> None:
    """Configure a USRP SDR's transmit antenna using the provided values.

    Only validates the gain value: type, value, and against the hardware's channel.
    """
    # INPUT VALIDATION
    _validate_usrp_tx_gain(usrp=usrp, gain_value=gain, channel=channel)
    # CONFIGURE IT
    usrp.set_tx_rate(samp_rate)
    usrp.set_tx_freq(center_freq)
    usrp.set_tx_gain(gain)
    tx_ant = usrp.get_tx_antennas(channel)
    usrp.set_tx_antenna(tx_ant[0], channel)  # TRX


def _validate_usrp_object(usrp: uhd.usrp.multi_usrp.MultiUSRP, param_name: str) -> None:
    """Validate a USRP object on behalf of this module."""
    validate_type(usrp, param_name, uhd.usrp.multi_usrp.MultiUSRP)


def _validate_usrp_rx_gain(usrp: uhd.usrp.multi_usrp.MultiUSRP, gain_value: float | int,
                           channel: int = 0) -> None:
    """Validate a USRP RX gain value against the hardware."""
    gain_range = usrp.get_rx_gain_range(channel)
    # Extract min, max, and step boundaries from the UHD range object
    min_gain = gain_range.start()  # Will return 0.0
    max_gain = gain_range.stop()   # Will return 76.0 for RX, 89.8 for TX
    if not (min_gain <= gain_value <= max_gain):
        raise ValueError(f'RX Gain {gain_value} db out of safe range: [{min_gain}, {max_gain}]')


def _validate_usrp_tx_gain(usrp: uhd.usrp.multi_usrp.MultiUSRP, gain_value: float | int,
                           channel: int = 0) -> None:
    """Validate a USRP RX gain value against the hardware."""
    gain_range = usrp.get_tx_gain_range(channel)
    # Extract min, max, and step boundaries from the UHD range object
    min_gain = gain_range.start()  # Will return 0.0
    max_gain = gain_range.stop()   # Will return 89.8 for TX
    step = gain_range.step()       # 0.25 for TX
    if not (min_gain <= gain_value <= max_gain):
        raise ValueError(f'TX Gain {gain_value} db out of safe range: [{min_gain}, {max_gain}]')
