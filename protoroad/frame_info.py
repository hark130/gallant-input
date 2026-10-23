"""Data types describing frames that are to be sent, were sent, received, or expected."""

# Standard Imports
from dataclasses import dataclass
from enum import IntEnum
from typing import Final
# Third Party Imports
# Local Imports
from protoroad.constants import BROADCAST_ADDR, MAX_DATA_LEN, SEQ_MODULUS, START_SEQ_NUM

_MAX_BYTE_VAL: Final[int] = 0xFF  # Maximum value for an 8-bit field
_SEQ_CYCLE: Final[int] = SEQ_MODULUS - START_SEQ_NUM  # Values actually used: 1..255 = 255


class MsgType(IntEnum):
    """Known values of the header's type field."""

    UNUSED = 0x00  # Unused/undefined
    DATA = 0x01    # Text message
    ACK = 0x02     # Acknowledgement (future: ALOHA/ARQ)


@dataclass(frozen=True)
class FrameInfo:
    """One frame's contents: header fields + message."""

    dst: int        # Destination node address; BROADCAST_ADDR for everyone
    src: int        # Source node address
    msg_type: int   # Header type field (use the MsgType IntEnum on TX)
    seq: int        # Sequence number, wraps at 255
    message: bytes  # Meaningful data bytes only (no pad, encoding, FEC, etc)

    def __post_init__(self):
        """Validate field ranges so a bad frame fails here, not deep in the modulator."""
        for name in ("dst", "src", "msg_type", "seq"):
            value = getattr(self, name)
            if not 0 <= value <= _MAX_BYTE_VAL:
                raise ValueError(f"{name} must fit in 8 bits, got {value}")
        if self.length > MAX_DATA_LEN:
            raise ValueError(f"message is {len(self.message)} bytes; max is {MAX_DATA_LEN}")

    @property
    def is_broadcast(self) -> bool:
        """True if addressed to every node."""
        return self.dst == BROADCAST_ADDR

    @property
    def length(self) -> int:
        """Payload length in bytes (what the header's length field carries)."""
        return len(self.message)

    @property
    def next_seq(self) -> int:
        """Determine the next expected sequence number that should follow this frame."""
        return get_next_seq(seq=self.seq)

    @property
    def text(self) -> str:
        """Payload as text; undecodable bytes show as U+FFFD instead of raising."""
        return self.message.decode("ascii", errors="replace")


def get_next_seq(seq: int) -> int:
    """Calculate the next expected sequence number to follow seq.

    The sequence number after seq: 1, 2, ..., 255, then back to 1 (0 is skipped).
    """
    seq = (seq + 1) % SEQ_MODULUS
    return START_SEQ_NUM if seq == 0 else seq


def measure_seq_nums(prev: int, seq: int) -> int:
    """Measure how many sequence numbers between prev and seq (0 means seq == prev).

    Example: measure_seq_nums(254, 2) == 3  (254 -> 255 -> 1 -> 2)
    """
    return (seq - prev) % _SEQ_CYCLE
