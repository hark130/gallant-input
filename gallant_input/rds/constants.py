"""Defines RDS specific constant values."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports


# See: https://en.wikipedia.org/wiki/Radio_Data_System#Baseband_coding_(Data-link_layer)
RDS_BLOCK_LEN: Final[int] = 26  # The lengh, in bits, of one RDS block
RDS_BLOCK_DATA_LEN: Final[int] = 16  # The lengh, in bits, of one RDS block data field
RDS_BLOCK_CWORD_LEN: Final[int] = 10  # The lengh, in bits, of one RDS block checkword field
RDS_BLOCKS_IN_GROUP: Final[int] = 4  # The number of RDS blocks in an RDS group
RDS_GROUP_LEN: Final[int] = RDS_BLOCK_LEN * RDS_BLOCKS_IN_GROUP  # The length, in bits, of a group

# Taken from RDS: The Radio Data System Appendix B: Table B.1 Binary Values of the RDS Offset Words
# See: https://www.iz3mez.it/wp-content/library/ebook/RDS%20-%20The%20Radio%20Data%20System.pdf
RDS_OFFSET_A: Final[bytes] = bytes('0011111100', 'utf-8')
RDS_OFFSET_B: Final[bytes] = bytes('0110011000', 'utf-8')
RDS_OFFSET_C: Final[bytes] = bytes('0101101000', 'utf-8')
RDS_OFFSET_C_PRIME: Final[bytes] = bytes('1101010000', 'utf-8')
RDS_OFFSET_D: Final[bytes] = bytes('0110110100', 'utf-8')
RDS_OFFSET_E: Final[bytes] = bytes('0000000000', 'utf-8')

# Taken from RDS: The Radio Data System Appendix B: B.3 Order of Bit Transmission,
# Error Protection, and Synchronisation Information
# RDS CRC polynomial
RDS_CRC_POLY: Final[bytes] = bytes('10110111001', 'utf-8')  # 0x5B9
