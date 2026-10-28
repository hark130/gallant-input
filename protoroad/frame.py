"""Functionality to build, parse, and forward error correct (FEC) frames."""

# Standard Imports
from dataclasses import dataclass
from enum import IntEnum
from typing import Final, NamedTuple
# Third Party Imports
import numpy as np
# Local Imports
from protoroad.constants import (BROADCAST_ADDR, HEADER_LEN, MAX_DATA_LEN, NULL_ADDR, PAD_BYTE,
                                 START_SEQ_NUM)
from protoroad.convert import (convert_bin_bytes_to_ascii, convert_int_to_binary,
                               convert_msg_to_binary)
from protoroad.crc import CRC_LEN, check_crc16, crc16_bytes
from protoroad.frame_info import FrameInfo, MsgType

_BIT_CHARS: Final[bytes] = b"01"  # The only valid characters in a bits bytes object
_MAX_ASCII: Final[int] = 0x7F  # Highest valid ASCII byte value


class DecodeStatus(IntEnum):
    """What happened when decoding one burst (why there is, or isn't, a frame)."""

    OK = 0         # Valid frame
    NO_SYNC = 1    # No syncword: noise, a false alarm, or a badly damaged frame
    TRUNCATED = 2  # Syncword found, but the burst ended before the frame did
    CRC_FAIL = 3   # Decoded, but the CRC didn't match: corrupted beyond what FEC could fix
    INVALID = 4    # CRC matched, but a header field or the padding was impossible


@dataclass(frozen=True)
class DecodeResult:
    """The outcome of decoding one burst, plus the measurements BER is calculated from.

    Returned even when decoding fails: failed frames are where the bit errors are.
    """

    status: DecodeStatus
    frame: FrameInfo | None = None  # Only when status is OK
    sync_errors: int = 0            # Bit errors in the syncword (0 if none was found)
    sync_bits: int = 0              # Syncword bits examined (0 if none was found)
    fec_disagreements: int = 0      # Coded bits that disagreed with their group's majority
    coded_bits: int = 0             # Coded (pre-FEC) bits examined
    raw: bytes = b""                # Decoded header + payload + CRC bytes (for true BER later)


class SyncMatch(NamedTuple):
    """Where a syncword was found, and whether it arrived inverted."""

    index: int       # Index in bits of the first syncword bit
    inverted: bool   # True if the syncword arrived inverted (180 degree ambiguity)
    errors: int = 0  # Bit errors in the received syncword (its Hamming distance)


def apply_fec(binary: bytes, repeats: int) -> bytes:
    """Apply FEC."""
    return b''.join(bytes([bit]) * repeats for bit in binary)


# pylint: disable=too-many-arguments,too-many-positional-arguments
def build_frame(preamble: bytes, syncword: bytes, header: bytes, payload: bytes,
                crc: bytes, fec_repeats: int, tail: bytes = b'00000000') -> bytes:
    """Build an entire frame: preamble + syncword + FEC(header + payload + CRC) + tail."""
    header = apply_fec(header, fec_repeats)
    data = apply_fec(payload, fec_repeats)
    crc = apply_fec(crc, fec_repeats)
    # If/when you interleave, interleave the header, data, and CRC here
    return preamble + syncword + header + data + crc + tail
# pylint: enable=too-many-arguments,too-many-positional-arguments


def build_frame_frameinfo(preamble: bytes, syncword: bytes, frameinfo: FrameInfo,
                          fec_repeats: int) -> bytes:
    """FrameInfo --> complete frame bits (preamble through tail)."""
    header = build_header(frameinfo.dst, frameinfo.src, frameinfo.msg_type,
                          frameinfo.seq, frameinfo.length)
    payload = build_payload(frameinfo.message)
    # CRC over the header + payload BYTES (before FEC), sent as bits like everything else
    crc = convert_msg_to_binary(crc16_bytes(convert_bin_bytes_to_ascii(header + payload)))
    return build_frame(preamble, syncword, header, payload, crc, fec_repeats)


def build_header(dst: int, src: int, msg_type: int, seq: int, msg_len: int) -> bytes:
    """Build the header.

    Args:
        dst: Destination node address; 0xFF for broadcast.
        src: This node address.
        type: [UNUSED] Type of message.
        seq: Sequence number.
        len: Length of the payload in bytes.
        fec_repeats: FEC repeats.
    """
    destination = convert_int_to_binary(dst)        # Destination node address
    source = convert_int_to_binary(src)             # Source node address
    message_type = convert_int_to_binary(msg_type)  # Use an IntEnum later
    seq_num = convert_int_to_binary(seq)            # Sequence number
    message_len = convert_int_to_binary(msg_len)    # Payload length in bytes
    header = destination + source + message_type + seq_num + message_len
    return header


def build_payload(message: bytes) -> bytes:
    """Build the payload from a meaningful message."""
    if len(message) > MAX_DATA_LEN:
        raise ValueError(f"Does not support messages of greater than {MAX_DATA_LEN} length.")
    message = message.ljust(MAX_DATA_LEN, PAD_BYTE)  # Pad to the maximum data length
    return convert_msg_to_binary(message)


def count_fec_disagreements(binary: bytes, repeats: int) -> int:
    """Count coded bits that disagree with their repetition group's majority vote.

    Each disagreeing copy is one channel bit error, so this estimates the raw (pre-FEC) bit
    errors without knowing what was sent.  It undercounts when a group has more errors than
    it can correct (e.g., 2 of 3 copies flipped counts as 1), so it reads low at high BER.
    """
    # LOCAL VARIABLES
    usable = len(binary) - len(binary) % repeats                      # Whole groups only
    bits = np.frombuffer(binary[:usable], dtype=np.uint8) - ord("0")  # 0/1 values
    ones = bits.reshape(-1, repeats).sum(axis=1)                      # 1s per group

    # DONE: the minority in each group disagreed with the majority
    return int(np.minimum(ones, repeats - ones).sum())


def decode_fec(binary: bytes, repeats: int) -> bytes:
    """Decode FEC."""
    decoded = bytearray()
    for i in range(0, len(binary), repeats):
        group = binary[i:i + repeats]
        ones = group.count(ord('1'))
        decoded.append(ord('1') if ones > repeats // 2 else ord('0'))
    return bytes(decoded)


def decode_frame(bits: bytes, syncword: bytes, fec_repeats: int,
                 max_errors: int = 2) -> DecodeResult:
    """Find the syncword in demodulated bits, decode the frame after it, and measure it.

    Example Usage:
        result = decode_frame(rx_bits, SYNCWORD, FEC_REPEATS)
        if result.status == DecodeStatus.OK:
            print(result.frame.text)

    Args:
        bits: Demodulated bits as a bytes object of b'0'/b'1' characters.
        syncword: The expected syncword, same format.
        fec_repeats: Repetition FEC factor the transmitter used.
        max_errors: [OPTIONAL] Most bit errors tolerated in the received syncword.

    Returns:
        A DecodeResult: the frame (if valid), why not (if not), and the error measurements.

    Raises:
        TypeError: bits or syncword isn't bytes.
        ValueError: Invalid syncword, max_errors, fec_repeats, or non-binary characters.
    """
    # LOCAL VARIABLES
    block_len = 0                  # Coded header + payload + CRC length (bits)
    match = None                   # Where the syncword is
    block = None                   # Coded header + payload + CRC bits
    raw = None                     # Decoded header + payload + CRC bytes
    frame = None                   # The frame, if valid
    status = DecodeStatus.NO_SYNC  # What happened

    # INPUT VALIDATION
    if fec_repeats < 1:
        raise ValueError(f"fec_repeats must be >= 1, got {fec_repeats}")

    # FIND IT
    block_len = (HEADER_LEN + MAX_DATA_LEN + CRC_LEN) * 8 * fec_repeats
    match = find_syncword(bits, syncword, max_errors)
    if match is None:
        return DecodeResult(status=status)
    block = bits[match.index + len(syncword):][:block_len]
    if len(block) < block_len:
        return DecodeResult(status=DecodeStatus.TRUNCATED, sync_errors=match.errors,
                            sync_bits=len(syncword))

    # FIX IT
    if match.inverted:
        block = invert_bits(block)
    raw = convert_bin_bytes_to_ascii(decode_fec(block, fec_repeats))

    # CHECK IT: CRC first (strongest check), then the field-by-field checks
    if not check_crc16(raw):
        status = DecodeStatus.CRC_FAIL
    else:
        frame = _validate_frame(raw[:-CRC_LEN])
        status = DecodeStatus.INVALID if frame is None else DecodeStatus.OK

    # DONE
    return DecodeResult(status=status, frame=frame, sync_errors=match.errors,
                        sync_bits=len(syncword),
                        fec_disagreements=count_fec_disagreements(block, fec_repeats),
                        coded_bits=len(block), raw=raw)


def find_syncword(bits: bytes, syncword: bytes, max_errors: int = 2) -> SyncMatch | None:
    """Find the first occurrence of the syncword, normal or inverted.

    Example Usage:
        match = find_syncword(rx_bits, SYNCWORD)
        if match is not None:
            block = rx_bits[match.index + len(SYNCWORD):]  # Header + payload start here
            if match.inverted:
                block = invert_bits(block)

    Correlates +/-1 versions of the bits and syncword.  For an N-bit syncword, a window with
    d bit errors correlates to N - 2d (or -(N - 2d) if inverted), so allowing max_errors is a
    correlation threshold of N - 2 * max_errors.

    Args:
        bits: Demodulated bits as a bytes object of b'0'/b'1' characters.
        syncword: The expected syncword, same format.
        max_errors: [OPTIONAL] Most bit errors tolerated in the received syncword.

    Returns:
        A SyncMatch, or None if no match was found.

    Raises:
        TypeError: bits or syncword isn't bytes.
        ValueError: Empty syncword, invalid max_errors, or non-binary characters.
    """
    # LOCAL VARIABLES
    num = len(syncword)               # Syncword length (bits)
    threshold = num - 2 * max_errors  # Minimum |correlation| for a match
    corr = None                       # Correlation at each offset
    hits = None                       # Offsets at or over the threshold
    first = 0                         # First offset at or over the threshold
    best = 0                          # Strongest offset near the first hit
    match = None                      # Return value

    # INPUT VALIDATION
    _validate_bits(syncword, "syncword")
    _validate_bits(bits, "bits")
    if num == 0:
        raise ValueError("syncword must not be empty")
    if not 0 <= max_errors < num / 2:
        # At N/2 errors a syncword and its inverse are indistinguishable
        raise ValueError(f"max_errors must be in [0, {num / 2}), got {max_errors}")
    if len(bits) >= num:
        # CORRELATE
        corr = np.correlate(_to_plus_minus(bits), _to_plus_minus(syncword), mode="valid")
        hits = np.flatnonzero(np.abs(corr) >= threshold)  # corr[i] compares bits[i:i + num]
        if hits.size != 0:
            # Pick the peak near the first hit, in case a neighboring offset also squeaked past
            first = int(hits[0])
            best = first + int(np.argmax(np.abs(corr[first:first + num])))
            match = SyncMatch(index=best, inverted=bool(corr[best] < 0),
                              errors=(num - abs(int(corr[best]))) // 2)

    # DONE
    return match


def invert_bits(bits: bytes) -> bytes:
    """Flip every bit: b'0' <--> b'1'.

    Use if 180 degree ambiguity is detected.
    """
    return bits.translate(bytes.maketrans(b"01", b"10"))


def parse_frame(bits: bytes, syncword: bytes, fec_repeats: int,
                max_errors: int = 2) -> FrameInfo | None:
    """Like decode_frame(), but return only the frame (None if anything went wrong)."""
    return decode_frame(bits, syncword, fec_repeats, max_errors).frame


def _to_plus_minus(bits: bytes) -> np.ndarray:
    """Map b'0'/b'1' characters to -1/+1 (int32, so correlation sums can't overflow)."""
    return 2 * (np.frombuffer(bits, dtype=np.uint8) - ord("0")).astype(np.int32) - 1


def _validate_bits(bits: bytes, name: str) -> None:
    """Raise if bits isn't a bytes object of only b'0'/b'1' characters."""
    if not isinstance(bits, bytes):
        raise TypeError(f"{name} must be bytes, got {type(bits).__name__}")
    if bits.translate(None, _BIT_CHARS):  # Anything left after deleting 0s and 1s
        raise ValueError(f"{name} contains characters other than b'0' and b'1'")


def _validate_frame(raw: bytes) -> FrameInfo | None:
    """Turn decoded header + payload bytes into a FrameInfo, or None if anything is invalid.

    FrameInfo enforces what a valid frame IS (addresses, sequence number, type, ASCII), for TX
    and RX alike.  This function only adds the wire-format checks FrameInfo can't see: the
    length field and the padding.
    """
    # LOCAL VARIABLES
    dst, src, msg_type, seq, length = raw[:HEADER_LEN]  # Header fields
    data = raw[HEADER_LEN:]                             # Padded payload
    frame = None                                        # The frame, if valid

    # VALIDATE IT
    if length <= MAX_DATA_LEN and data[length:] == PAD_BYTE * (MAX_DATA_LEN - length):
        try:
            frame = FrameInfo(dst=dst, src=src, msg_type=msg_type, seq=seq,
                              message=data[:length])
        except ValueError:
            pass  # A field FrameInfo rejects: frame stays None (log the reason here later)

    # DONE
    return frame
