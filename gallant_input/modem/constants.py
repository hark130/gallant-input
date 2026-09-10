"""Defines modem specific constant values."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports


# DEFAULT BITS --> SYMBOL MAPPINGS
# Amplitude Modulation (AM)
OOK_MAP: Final[dict[int, float]] = {0: 0.0, 1: 1.0}

# Frequency Modulation (FM)
# FSK2_MAP: Final[dict[int, float]] = {0: -baud_rate / 2, 1: baud_rate / 2}
FSK2_MAP: Final[dict[int, float]] = {0: -115200 / 2, 1: 115200 / 2}  # Baud Rate: 115200

# Phase Modulation (PM)
BPSK_MAP: Final[dict[int, complex]] = {0: -1+0j, 1: 1+0j}
BPSK_MAP_3GPP_5G: Final[dict[int, complex]] = {0: 1+0j, 1: -1+0j}  # 3GPP 5G standard
BPSK_MAP_802_11: Final[dict[int, complex]] = {0: -1+0j, 1: 1+0j}  # IEEE 802.11 standard
# Default QPSK mapping
QPSK_MAP: Final[dict[int, complex]] = {0b00: 1+1j, 0b01: -1+1j, 0b10: 1-1j, 0b11: -1-1j}
# QPSK mapping used in Digital Video Broadcasting (DVB) - Satellite Second Generation (S2) standard
QPSK_MAP_DVB_S2: Final[dict[int, complex]] = {0b00: 1+1j, 0b01: 1-1j, 0b10: -1+1j, 0b11: -1-1j}
# 8-PSK gray coded (and reasonably normalized) mapping
PSK8_MAP: Final[dict[int, complex]] = {
    0b000: 1.0000+0.0000j,   # 0 degrees (0 rad)
    0b001: 0.7071+0.7071j,   # 45 degrees (pi/4 rad)
    0b011: 0.0000+1.0000j,   # 90 degrees (pi/2 rad)
    0b010: -0.7071+0.7071j,  # 135 degrees (3pi/4 rad)
    0b110: -1.0000+0.0000j,  # 180 degrees (pi rad)
    0b111: -0.7071-0.7071j,  # 225 degrees (5pi/4 rad)
    0b101: 0.0000-1.0000j,   # 270 degrees (3pi/2 rad)
    0b100: 0.7071-0.7071j    # 315 degrees (7pi/4 rad)
}

# Hybrid Modulation
# 16-QAM gray coded constellation diagram
QAM16_MAP: Final[dict[int, complex]] = {
    0b0000: (-3-3j), 0b0001: (-3-1j), 0b0010: (-3+1j), 0b0011: (-3+3j),
    0b0100: (-1-3j), 0b0101: (-1-1j), 0b0110: (-1+1j), 0b0111: (-1+3j),
    0b1000: (1-3j),  0b1001: (1-1j),  0b1010: (1+1j),  0b1011: (1+3j),
    0b1100: (3-3j),  0b1101: (3-1j),  0b1110: (3+1j),  0b1111: (3+3j),
}
