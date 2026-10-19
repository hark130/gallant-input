"""Single point of truth (SPOT) macros."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports
from protoroad.convert import convert_hex_str_to_binary

FEC_REPEATS: Final[int] = 3
PREAMBLE: Final[bytes] = b"10" * 32
SYNCWORD: Final[bytes] = convert_hex_str_to_binary("0x1ACFFC1D")
