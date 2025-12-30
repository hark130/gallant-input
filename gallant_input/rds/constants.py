"""Defines RDS specific constant values."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports


# Taken from RDS: The Radio Data System Appendix B Table B.1 Binary Values of the RDS Offset Words
# See: https://www.iz3mez.it/wp-content/library/ebook/RDS%20-%20The%20Radio%20Data%20System.pdf
RDS_BLOCK_LEN: Final[int] = 26  # The lengh, in bits, of one RDS block
RDS_OFFSET_A: Final[bytes] = bytes('0011111100', 'utf-8')
RDS_OFFSET_B: Final[bytes] = bytes('0110011000', 'utf-8')
RDS_OFFSET_C: Final[bytes] = bytes('0101101000', 'utf-8')
RDS_OFFSET_C_PRIME: Final[bytes] = bytes('1101010000', 'utf-8')
RDS_OFFSET_D: Final[bytes] = bytes('0110110100', 'utf-8')
RDS_OFFSET_E: Final[bytes] = bytes('0000000000', 'utf-8')
