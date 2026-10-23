"""Single point of truth (SPOT) macros."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports
from protoroad.convert import convert_hex_str_to_binary

BPSK_MAP: Final[dict[int, complex]] = {0: -1+0j, 1: 1+0j}
BROADCAST_ADDR: Final[int] = 0xFF  # Destination address meaning "every node"
EXIT_FAIL: Final[int] = 1
EXIT_SUCCESS: Final[int] = 0
FEC_REPEATS: Final[int] = 3
HEADER_LEN: Final[int] = 5  # Header length in bytes: dst, src, type, seq, len
LOG_STR_RX: Final[str] = "[RX] {action} - {message}"  # Receiver format string
LOG_STR_TX: Final[str] = "[TX] {action} - {message}"  # Transmit format string
MAX_DATA_LEN: Final[int] = 32  # Maximum length, in bytes, of one decoded payload (max len(message))
PAD_BYTE: Final[bytes] = b" "  # Pads short payloads to MAX_DATA_LEN (also use in build_payload)
PREAMBLE: Final[bytes] = b"10" * 32
SYNCWORD: Final[bytes] = convert_hex_str_to_binary("0x4954CE1F")  # Alternate: 0x0C9BCA57
