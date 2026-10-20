"""Entry point."""

# Standard Imports
from typing import Final
import sys
# Third Party Imports
# Local Imports
from protoroad.bpsk import BPSK
from protoroad.constants import BPSK_MAP, EXIT_FAIL, EXIT_SUCCESS, FEC_REPEATS, PREAMBLE, SYNCWORD
from protoroad.convert import (convert_bin_bytes_to_ascii, convert_bit_array_to_ascii,
                               convert_bit_array_to_bytes, convert_msg_to_binary)
from protoroad.frame import build_frame, build_header, build_payload

PROTOCOL_SPS: Final[int] = 4  # The protocol's samples-per-symbol
PROTOCOL_BAUD: Final[int] = 250_000  # The protocol's symbol rate
PROTOCOL_SAMP_RATE: Final[int] = PROTOCOL_SPS * PROTOCOL_BAUD
TEST_MESSAGE: Final[bytes] = b"This is my test input.  Mine?!?"  # 32 bytes of 'known' message
UNUSED_FIELD: Final[int] = 0xAA  # Value for unused 8-bit header fields


def main() -> int:
    """do_it()."""
    # LOCAL VARIABLES
    exit_code = EXIT_SUCCESS   # Exit status
    fec_repeats = FEC_REPEATS  # FEC Repeats
    preamble = PREAMBLE        # Preamble
    syncword = SYNCWORD        # Syncword
    header = b''               # The header
    payload = b''              # The payload
    message = TEST_MESSAGE     # The message used to form the payload
    mapping = BPSK_MAP         # The constellation diagram
    sps = PROTOCOL_SPS         # Samples per symbol
    baud = PROTOCOL_BAUD       # Symbol rate
    modem = BPSK(mapping=mapping, samples_per_symbol=sps, symbol_rate=baud)

    # DO IT
    payload = build_payload(message)
    header = build_header(dst=UNUSED_FIELD, src=UNUSED_FIELD, msg_type=UNUSED_FIELD,
                          seq=UNUSED_FIELD, msg_len=len(message))
    frame = build_frame(preamble=preamble, syncword=syncword, header=header, payload=payload,
                        fec_repeats=fec_repeats)
    samples = modem.modulate(binary=convert_msg_to_binary(message))
    result = convert_bit_array_to_bytes(modem.demodulate(samples=samples))
    print(f"ORIGINAL:  {message}")  # DEBUGGING
    print(f"MOD/DEMOD: {convert_bin_bytes_to_ascii(result[::sps])}")  # DEBUGGING

    # DONE
    return exit_code
