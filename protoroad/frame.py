"""Functionality to build, parse, and forward error correct (FEC) frames."""

# Standard Imports
# Third Party Imports
# Local Imports
from protoroad.convert import convert_int_to_binary


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
    destination = convert_int_to_binary(dst)      # Destination node address
    source = convert_int_to_binary(src)           # Source node address
    message_type = convert_int_to_binary(type)    # Use an IntEnum later
    seq_num = convert_int_to_binary(seq)          # Sequence number
    message_len = convert_int_to_binary(msg_len)  # Payload length in bytes
    header = destination + source + message_type + seq_num + message_len
    return header


def build_frame(preamble: bytes, syncword: bytes, header: bytes, payload: bytes,
                fec_repeats: int, tail: bytes = b'00000000') -> bytes:
    """Build an entire frame."""
    header = apply_fec(header, fec_repeats)
    data = apply_fec(payload, fec_repeats)
    return preamble + syncword + header + data + tail


def build_payload(payload: bytes) -> bytes:
    """Build the payload."""
    return payload


def decode_fec(binary: bytes, repeats: int) -> bytes:
    """Decode FEC."""
    decoded = bytearray()
    for i in range(0, len(binary), repeats):
        group = binary[i:i + repeats]
        ones = group.count(ord('1'))
        decoded.append(ord('1') if ones > repeats // 2 else ord('0'))
    return bytes(decoded)


