"""Defines the FrameTransmitter class: the TX chain, from FrameInfo to a burst on the air.

    FrameInfo -> frame bits (preamble + syncword + FEC'd header/payload + tail)
        -> modulation (map + zero-stuff) -> pulse shaping (RRC) -> radio burst

FrameTransmitter also owns this node's identity on the channel: its source address and the
sequence number it stamps on each frame it sends.
"""

# Standard Imports
# Third Party Imports
import numpy as np
# Local Imports
from protoroad.bpsk import BPSK
from protoroad.constants import BROADCAST_ADDR, NULL_ADDR, START_SEQ_NUM
from protoroad.frame import build_frame_frameinfo
from protoroad.frame_info import FrameInfo, MsgType


class FrameTransmitter:
    """Turn frames into pulse-shaped bursts and send them through a radio."""

    # pylint: disable=too-many-arguments,too-many-positional-arguments
    def __init__(self, radio, modem: BPSK, rrc_taps: np.ndarray, preamble: bytes,
                 syncword: bytes, fec_repeats: int, address: int):
        """Class ctor.

        Args:
            radio: Anything with transmit(samples) -> int (e.g., protoroad.radio.Radio).
            modem: Modulator (its mapping must match the receivers').
            rrc_taps: RRC taps, the same ones the receivers' matched filters use.
            preamble: The protocol's preamble, as b'0'/b'1' characters.
            syncword: The protocol's syncword, as b'0'/b'1' characters.
            fec_repeats: Repetition FEC factor.
            address: This node's address, stamped as src on every frame it sends.
        """
        # INPUT VALIDATION
        if not NULL_ADDR < address < BROADCAST_ADDR:  # The broadcast address is never a source
            raise ValueError(f"address must be in [0, 0xFE], got {address}")

        # TX CHAIN
        self._radio = radio
        self._modem = modem
        self._rrc_taps = rrc_taps

        # PROTOCOL
        self._preamble = preamble
        self._syncword = syncword
        self._fec_repeats = fec_repeats

        # THIS NODE
        self._address = address         # Source address of every frame sent
        self._next_seq = START_SEQ_NUM  # Sequence number for the next frame (wraps at SEQ_MODULUS)
    # pylint: enable=too-many-arguments,too-many-positional-arguments

    @property
    def address(self) -> int:
        """This node's address."""
        return self._address

    def build_samples(self, frame: FrameInfo) -> np.ndarray:
        """Build the pulse-shaped baseband burst for one frame (no radio involved).

        Useful on its own for tests and for saving captures.
        """
        bits = build_frame_frameinfo(preamble=self._preamble, syncword=self._syncword,
                                     frameinfo=frame, fec_repeats=self._fec_repeats)
        shaped = np.convolve(self._modem.modulate(binary=bits), self._rrc_taps)  # Pulse shaping
        return shaped.astype(np.complex64)

    def send(self, frame: FrameInfo) -> int:
        """Transmit one frame as one burst.

        Returns:
            Number of samples the radio sent (including its tail padding).
        """
        return self._radio.transmit(samples=self.build_samples(frame))

    def send_message(self, dst: int, message: bytes,
                     msg_type: MsgType = MsgType.DATA) -> FrameInfo:
        """Stamp a new frame with this node's address and the next sequence number; send it.

        Args:
            dst: Destination address (BROADCAST_ADDR for everyone).
            message: Message to transmit as a byte string (at most MAX_DATA_LEN in length).
            msg_type: [OPTIONAL] Header type field.

        Returns:
            The FrameInfo that was sent (e.g., to log it, or to match an ACK against later).
        """
        frame = FrameInfo(dst=dst, src=self._address, msg_type=msg_type, seq=self._next_seq,
                          message=message)
        self.send(frame)
        self._next_seq = frame.next_seq
        return frame
