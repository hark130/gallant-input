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
QPSK_MAP: Final[dict[int, complex]] = {0b00: 1+1j, 0b01: -1+1j, 0b10: 1-1j, 0b11: -1-1j}
