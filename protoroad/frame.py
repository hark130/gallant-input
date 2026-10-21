"""Functionality to build, parse, and forward error correct (FEC) frames."""

# Standard Imports
from typing import Final, NamedTuple
# Third Party Imports
import numpy as np
# Local Imports
from protoroad.constants import HEADER_LEN, MAX_DATA_LEN, PAD_BYTE
from protoroad.convert import (convert_bin_bytes_to_ascii, convert_int_to_binary,
                               convert_msg_to_binary)
from protoroad.frame_info import FrameInfo, MsgType

_BIT_CHARS: Final[bytes] = b"01"  # The only valid characters in a bits bytes object
_MAX_ASCII: Final[int] = 0x7F  # Highest valid ASCII byte value


class SyncMatch(NamedTuple):
    """Where a syncword was found, and whether it arrived inverted."""

    index: int      # Index in bits of the first syncword bit
    inverted: bool  # True if the syncword arrived inverted (180 degree ambiguity)


def apply_fec(binary: bytes, repeats: int) -> bytes:
    """Apply FEC."""
    return b''.join(bytes([bit]) * repeats for bit in binary)


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


def build_frame(preamble: bytes, syncword: bytes, header: bytes, payload: bytes,
                fec_repeats: int, tail: bytes = b'00000000') -> bytes:
    """Build an entire frame."""
    header = apply_fec(header, fec_repeats)
    data = apply_fec(payload, fec_repeats)
    # If/when you interleave, interleave the header and data here
    return preamble + syncword + header + data + tail


def build_frame_frameinfo(preamble: bytes, syncword: bytes, frameinfo: FrameInfo,
                          fec_repeats: int) -> bytes:
    """FrameInfo --> complete frame bits (preamble through tail)."""
    header = build_header(frame.dst, frame.src, frame.msg_type, frame.seq, frame.length)
    return build_frame(preamble, syncword, header, build_payload(frame.payload), fec_repeats)


def build_payload(payload: bytes) -> bytes:
    """Build the payload."""
    if len(payload) > MAX_DATA_LEN:
        raise ValueError(f"Does not support messages of greater than {MAX_DATA_LEN} length.")
    payload = payload.ljust(32, b" ")  # Pad to a minimum length of 32 bytes
    return convert_msg_to_binary(payload)


def decode_fec(binary: bytes, repeats: int) -> bytes:
    """Decode FEC."""
    decoded = bytearray()
    for i in range(0, len(binary), repeats):
        group = binary[i:i + repeats]
        ones = group.count(ord('1'))
        decoded.append(ord('1') if ones > repeats // 2 else ord('0'))
    return bytes(decoded)


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
            match = SyncMatch(index=best, inverted=bool(corr[best] < 0))

    # DONE
    return match


def invert_bits(bits: bytes) -> bytes:
    """Flip every bit: b'0' <--> b'1'.

    Use if 180 degree ambiguity is detected.
    """
    return bits.translate(bytes.maketrans(b"01", b"10"))


def parse_frame(bits: bytes, syncword: bytes, fec_repeats: int,
                max_errors: int = 2) -> FrameInfo | None:
    """Find the syncword in demodulated bits and decode the frame that follows it.

    Only tries the first syncword match.  The real frame may be missed if its hidden behind a
    false match.

    Example Usage:
        frame = parse_frame(rx_bits, SYNCWORD, FEC_REPEATS)
        if frame is not None:
            print(frame.text)

    Args:
        bits: Demodulated bits as a bytes object of b'0'/b'1' characters.
        syncword: The expected syncword, same format.
        fec_repeats: Repetition FEC factor the transmitter used.
        max_errors: [OPTIONAL] Most bit errors tolerated in the received syncword.

    Returns:
        The decoded FrameInfo, or None if no syncword was found, the frame was truncated, or
        the decoded frame failed validation (see _validate_frame()).

    Raises:
        TypeError: bits or syncword isn't bytes.
        ValueError: Invalid syncword, max_errors, fec_repeats, or non-binary characters.
    """
    # LOCAL VARIABLES
    block_len = 0  # Coded header + payload length (bits)
    match = None   # Where the syncword is
    block = None   # Coded header + payload bits
    raw = None     # Decoded header + payload bytes
    frame = None   # Return value

    # INPUT VALIDATION
    if fec_repeats < 1:
        raise ValueError(f"fec_repeats must be >= 1, got {fec_repeats}")

    # FIND IT
    block_len = (HEADER_LEN + MAX_DATA_LEN) * 8 * fec_repeats
    match = find_syncword(bits, syncword, max_errors)
    if match is not None:
        block = bits[match.index + len(syncword):][:block_len]
        if len(block) == block_len:  # Otherwise, the frame was truncated
            # FIX IT
            if match.inverted:
                block = invert_bits(block)
            raw = convert_bin_bytes_to_ascii(decode_fec(block, fec_repeats))
            # CHECK IT
            frame = _validate_frame(raw)

    # DONE
    return frame


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

    Without a CRC these checks are the only defense against false syncs and miscorrected
    bits, so they're deliberately strict.
    """
    # LOCAL VARIABLES
    dst, src, msg_type, seq, length = raw[:HEADER_LEN]  # Header fields
    data = raw[HEADER_LEN:]                             # Padded payload

    # VALIDATE IT
    if length > MAX_DATA_LEN:
        return None  # Impossible length: garbage or a corrupted header
    try:
        MsgType(msg_type)
    except ValueError:
        return None  # Unknown message type
    if data[length:] != PAD_BYTE * (MAX_DATA_LEN - length):
        return None  # Padding must be untouched
    if any(byte > _MAX_ASCII for byte in data[:length]):
        return None  # Non-ASCII payload byte: corrupted

    # DONE
    return FrameInfo(dst=dst, src=src, msg_type=msg_type, seq=seq, payload=data[:length])
