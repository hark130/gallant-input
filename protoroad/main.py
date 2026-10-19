"""Entry point."""

# Standard Imports
import sys
# Third Party Imports
# Local Imports
from protoroad.constants import EXIT_FAIL, EXIT_SUCCESS, FEC_REPEATS, PREAMBLE, SYNCWORD
from protoroad.frame import build_frame, build_header, build_payload


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

    # DO IT
    payload = build_payload(message)
    header = build_header(dst=UNUSED_FIELD, src=UNUSED_FIELD, type=UNUSED_FIELD, seq=UNUSED_FIELD,
                          msg_len=len(message))
    frame = build_frame(preamble=preamble, syncword=syncword, header=header, payload=payload,
                        fec_repeats=fec_repeats)

    # DONE
    return exit_code
