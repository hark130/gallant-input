"""Data types describing frames: what was sent, and how it was received."""

# Standard Imports
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Final
import time
# Third Party Imports
# Local Imports
from protoroad.constants import MAX_DATA_LEN

BROADCAST_ADDR: Final[int] = 0xFF  # Destination address meaning "every node"
_MAX_BYTE_VAL: Final[int] = 0xFF  # Maximum value for an 8-bit field


class MsgType(IntEnum):
    """Known values of the header's type field."""

    UNUSED = 0x00  # Unused/undefined
    DATA = 0x01    # Text message
    ACK = 0x02     # Acknowledgement (future: ALOHA/ARQ)


@dataclass(frozen=True)
class FrameInfo:
    """One frame's contents: header fields + payload."""

    dst: int           # Destination node address; BROADCAST_ADDR for everyone
    src: int           # Source node address
    msg_type: MsgType  # Header type field
    seq: int           # Sequence number, wraps at 255
    payload: bytes     # Meaningful payload bytes only (header length applied, no pad)

    def __post_init__(self):
        """Validate field ranges so a bad frame fails here, not deep in the modulator."""
        for name in ("dst", "src", "msg_type", "seq"):
            value = getattr(self, name)
            if not 0 <= value <= _MAX_BYTE_VAL:
                raise ValueError(f"{name} must fit in 8 bits, got {value}")
        if self.length > MAX_DATA_LEN:
            raise ValueError(f"payload is {len(self.payload)} bytes; max is {MAX_DATA_LEN}")

    @property
    def length(self) -> int:
        """Payload length in bytes (what the header's length field carries)."""
        return len(self.payload)

    @property
    def text(self) -> str:
        """Payload as text; undecodable bytes show as U+FFFD instead of raising."""
        return self.payload.decode("ascii", errors="replace")

    @property
    def is_broadcast(self) -> bool:
        """True if addressed to every node."""
        return self.dst == BROADCAST_ADDR
