"""Defines the FrameReceiver class and frame_receiver(): the RX DSP chain, end to end.

FrameReceiver turns a stream of raw complex samples (any chunk size) into decoded frames:

    matched filter --> burst detection --> AGC --> timing recovery --> carrier recovery
        --> demodulation --> frame sync + FEC + parse

The matched filter and burst detector run on every sample (both are stateful, so chunk
boundaries don't matter).  Everything after them runs once per burst, in burst mode: each
burst gets a fresh AGC level, timing loop, and Costas loop, locked on its own preamble.

frame_receiver() is the thread body that feeds FrameReceiver from the radio.
"""

# Standard Imports
from typing import Callable, Final
import threading
# Third Party Imports
import numpy as np
# Local Imports
from protoroad.agc import AGC
from protoroad.bpsk import BPSK
from protoroad.burst_detector import BurstDetector
from protoroad.constants import BROADCAST_ADDR, LOG_STR_RX
from protoroad.convert import convert_bit_array_to_bytes
from protoroad.costas_loop import CostasLoop
from protoroad.frame import parse_frame
from protoroad.frame_info import FrameInfo
from protoroad.matched_filter import MatchedFilter
from protoroad.timing_recovery import GardnerTimingRecovery

DEFAULT_COSTAS_BW: Final[float] = 0.05  # Pulls in the worst-case +/-3.7 kHz radio-pair offset
DEFAULT_MIN_BURST: Final[int] = 2_000   # Samples; a frame is ~4,000, so this rejects blips


# pylint: disable=too-many-instance-attributes
class FrameReceiver:
    """Stateful RX chain: feed it consecutive chunks of raw samples, get back decoded frames."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, modem: BPSK, rrc_taps: np.ndarray, sps: int, syncword: bytes,
                 fec_repeats: int, pre_pad: int, min_burst: int = DEFAULT_MIN_BURST,
                 costas_bw: float = DEFAULT_COSTAS_BW):
        """Class ctor.

        Args:
            modem: Demodulator (its mapping must match the transmitter's).
            rrc_taps: RRC taps, the same ones the transmitter pulse-shapes with.
            sps: Samples per symbol.
            syncword: The protocol's syncword, as b'0'/b'1' characters.
            fec_repeats: Repetition FEC factor.
            pre_pad: Samples the burst detector keeps before each detected start.
            min_burst: [OPTIONAL] Shortest burst (samples) worth trying to decode.
            costas_bw: [OPTIONAL] Costas loop bandwidth; wider pulls in larger frequency offsets.
        """
        # PER-SAMPLE STAGES (stateful across chunks)
        self._matched_filter = MatchedFilter(rrc_taps)
        self._burst_detector = BurstDetector(min_len=min_burst, pre_pad=pre_pad)

        # PER-BURST STAGES (fresh for every burst)
        self._agc = AGC()
        self._timing = GardnerTimingRecovery(sps=sps)
        self._costas_bw = costas_bw  # CostasLoop has no reset(), so build one per burst

        # PROTOCOL
        self._modem = modem
        self._syncword = syncword
        self._fec_repeats = fec_repeats
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    def flush(self) -> list[FrameInfo]:
        """Decode a burst still open at the end of the stream (e.g., end of a capture file)."""
        return self._decode_bursts(self._burst_detector.flush())

    def process(self, chunk: np.ndarray) -> list[FrameInfo]:
        """Process the next chunk of raw samples.

        Args:
            chunk: 1-D complex samples, contiguous with the previous chunk.

        Returns:
            Frames decoded from bursts that ended in this chunk (possibly empty).
        """
        chunk = np.asarray(chunk, dtype=np.complex64)
        if chunk.size == 0:
            return []  # e.g., a recv() timeout; lfilter() can't take an empty array
        filtered = self._matched_filter.process(chunk)
        return self._decode_bursts(self._burst_detector.process(filtered))

    def _decode_bursts(self, bursts: list) -> list[FrameInfo]:
        """Run each complete burst through the rest of the chain; keep the valid frames."""
        # LOCAL VARIABLES
        frames = []  # Decoded frames

        # DECODE EACH BURST
        for burst in bursts:
            symbols = self._agc.normalize(burst.samples)        # Symbols near +/-1
            symbols = self._timing.recover(symbols)             # 1 sample per symbol
            symbols = CostasLoop(loop_bandwidth=self._costas_bw).process(symbols)  # Derotate
            bits = convert_bit_array_to_bytes(self._modem.demodulate(symbols))
            frame = parse_frame(bits, self._syncword, self._fec_repeats)
            if frame is not None:  # None: false alarm, noise, or a frame too damaged to trust
                frames.append(frame)

        # DONE
        return frames
# pylint: enable=too-many-instance-attributes


def frame_receiver(radio, receiver: FrameReceiver, stop_event: threading.Event,
                   on_frame: Callable[[FrameInfo, bool], None], address: int | None = None,
                   debug: bool = False) -> None:
    """Thread body: pull samples from the radio, decode frames, hand each one to on_frame.

    Args:
        radio: Anything with start_receiving(), receive() -> chunk, and stop_receiving().
        receiver: The FrameReceiver to feed.
        stop_event: Set it to make this function return.
        on_frame: Called with each decoded FrameInfo (e.g., print_frame).
        address: [OPTIONAL] If defined with an integer, will drop any frames whose src matches
            this value.
        debug: [OPTIONAL] If True, enables more verbose logging.
    """
    # RECEIVE IT
    radio.start_receiving()
    try:
        while not stop_event.is_set():
            for frame in receiver.process(radio.receive()):
                if address is None or _accept(frame_info=frame, address=address, debug=debug):
                    on_frame(frame, debug)
    finally:
        radio.stop_receiving()  # Always stop the stream, even on an exception


def _accept(frame_info: FrameInfo, address: int, debug: bool) -> bool:
    """Prints relevant log message and indicates whether or not to call on_frame()."""
    # LOCAL VARIABLES
    accepted = False  # Whether to call on_frame()

    # ACCEPT IT?
    if frame_info is not None:
        if frame_info.src == address and frame_info.dst != address:
            if debug:  # Our own transmission (self-addressed test frames still get through)
                print(LOG_STR_RX.format(action="Dropping", message=f"My own seq #{frame_info.seq}"))
        elif frame_info.dst in (address, BROADCAST_ADDR):
            accepted = True
            print(LOG_STR_RX.format(action="Receiving",
                                    message=f"Src addr #{frame_info.src} Seq #{frame_info.seq}"))
        elif debug:  # We didn't send it and it isn't for us
            print(LOG_STR_RX.format(action="Dropping", message=f"Frame for addr #{frame_info.dst}"))

    # DONE
    return accepted
