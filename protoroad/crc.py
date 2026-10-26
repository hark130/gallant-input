"""CRC-16 for protoroad frames: detect corruption that FEC missed (or miscorrected).

Variant: CRC-16/CCITT-FALSE.  Polynomial 0x1021 (x^16 + x^12 + x^5 + 1), initial value
0xFFFF, no input/output reflection, no final XOR.  Check value: crc16(b"123456789") == 0x29B1.
"""

# Standard Imports
from typing import Final
import binascii
# Third Party Imports
# Local Imports

CRC_INIT: Final[int] = 0xFFFF  # CCITT-FALSE initial value
CRC_LEN: Final[int] = 2        # CRC length in bytes (16 bits)
CRC_POLY: Final[int] = 0x1021  # x^16 + x^12 + x^5 + 1 (the x^16 term is implied)


def crc16(data: bytes) -> int:
    """CRC-16/CCITT-FALSE of data (uses the C implementation in Python's standard library)."""
    return binascii.crc_hqx(data, CRC_INIT)


def crc16_bytes(data: bytes) -> bytes:
    """crc16(data) as CRC_LEN bytes, big-endian (most significant byte first, like the bits)."""
    return crc16(data).to_bytes(CRC_LEN, "big")


def check_crc16(data_with_crc: bytes) -> bool:
    """True if the last CRC_LEN bytes are the correct CRC of everything before them."""
    if len(data_with_crc) < CRC_LEN:
        return False
    return crc16_bytes(data_with_crc[:-CRC_LEN]) == data_with_crc[-CRC_LEN:]
