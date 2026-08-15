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
