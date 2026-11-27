"""Defines a state machine to parse validated frames from received samples."""

# Standard Imports
from collections.abc import Callable
from enum import auto, Enum
from typing import Final
# Third Party Imports
import numpy
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_ndarray
from gallant_input.modem.calc import calculate_ber
from gallant_input.modem.modem import Modem
from gallant_input.synch.frame import find_frame_start
from rxtx.utilities import decode_fec_repetition


class FrameState(Enum):
    """The FrameReceiver state."""
    SEARCHING = auto()
    FULL_DECODE = auto()


# pylint: disable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
class FrameReceiver:
    """A symbol-->frame state machine.

    Receives continuous-valued, time scynch'd, symbol metrics in chunks, correlate syncwords,
    verify data integrity, and print payloads.
    """

    SYNCWORD_BITS = 32
    DATA_LEN_BITS = 8
    CHECKSUM_BITS = 8
    MAX_DATA_FIELD_BYTES: Final[int] = 32  # Max width of the DATA field in bytes (not counting FEC)
    # The DATA field is of variable length, as determined by the DATA_LEN field

    def __init__(self, modem: Modem, syncword: bytes, checksum: Callable[[bytes], int],
                 fec_repeat: int | None, max_data_bytes: int = 32, debug: bool = False):
        """Class ctor."""
        # Constructor arguments stored in attributes
        self._modem = modem                    # Modem() object
        self._syncword = syncword              # Expected binary syncword
        self._checksum = checksum              # Checksum generating function
        self._fec_repeat = fec_repeat          # Forward Error Correction value
        self._max_data_bytes = max_data_bytes  # Maximum size of the DATA field in bytes
        self._debug = debug                    # Caller desires debug output

        # Attributes updated during execution
        self._sync_arr = None                  # Syncword converted to a bipolar for correlation
        self._state = FrameState.SEARCHING     # The state of the state machine
        self._data_length = None               # DATA_LEN converted from binary to an integer
        # Symbols waiting to be processed
        self._buffer = numpy.empty(0, dtype=numpy.float32)

        # Debug mode counters
        self._count_syn = 0  # [CFT] Total count of syncword detections
        self._count_len = 0  # [CFT] Total count of valid DATA_LEN detections
        self._count_chk = 0  # [CFT] Total count of checksum passes

    def __del__(self):
        """Class dtor."""
        try:
            if self._debug is True:
                print(f'[CFT] The current state is {self._state.name}')
                print(f'[CFT] Found {self._count_syn} syncwords')
                print(f'[CFT] Found {self._count_len} DATA_LEN fields')
                print(f'[CFT] Found {self._count_chk} frames')
        except AttributeError:
            pass  # If the constructor failed, this attribute won't exist

    def process(self, symbol_metrics: numpy.ndarray, exp_data: bytes | None = None) -> list[bytes]:
        """Process a chunk of symbol metrics and return any complete frames.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.
            exp_data: [OPTIONAL] If defined, bit error rates (BERs) will
                be calculated and printed, in debug mode, for the syncwords and data based on the
                expected data provided.
        """
        # LOCAL VARIABLES
        datum = []  # A list of all the data fields currently found

        # PREPARE
        if self._sync_arr is None:
            self._sync_arr = convert_bin_bytes_to_ndarray(self._syncword,
                                                          bipolar=True).astype(numpy.float32)

        # PROCESS IT
        # Add the new input to the buffer
        self._buffer = numpy.concatenate([self._buffer, numpy.asarray(symbol_metrics,
                                          dtype=numpy.float32)])
        # Start state-machining
        while True:
            if self._state is FrameState.SEARCHING:
                frame_found = self._find_frame()
                if not frame_found:
                    break
            if self._state is FrameState.FULL_DECODE:
                data = self._full_decode(exp_data=exp_data)
                if data is None:
                    if self._state is FrameState.FULL_DECODE:
                        break  # Waiting on more samples
                    continue  # State was reset internally so keep going
                datum.append(data)  # Found one
                self._reset()  # Continue looking

        # DONE
        return datum

    def _find_frame(self) -> bool:
        """Search the buffered symbol metrics for the preamble."""
        # LOCAL VARIABLES
        frame_found = False  # Did we find a frame?
        start = None         # Index into symbol_metrics where the preamble begins

        # FIND IT
        # Find Syncword
        if self._buffer.size >= self.SYNCWORD_BITS:
            start = find_frame_start(symbol_metrics=self._buffer, preamble=self._sync_arr,
                                     threshold=0.65)
            if start is None:
                # No syncword found...
                keep = self.SYNCWORD_BITS - 1  # ...but keep enough symbols in case it was split
                if self._buffer.size > keep:
                    self._buffer = self._buffer[-keep:]  # Keeping the last "keep" bits
            else:
                if self._debug:
                    print('[CFT] Correlated a syncword')
                self._buffer = self._buffer[start:]  # Discard everything before the syncwords
                self._state = FrameState.FULL_DECODE  # Test a full decode
                frame_found = True  # Found one!

        # DONE
        return frame_found

    def _full_decode(self, exp_data: bytes | None) -> bytes | None:
        """Decode the entire frame and parse."""
        data = None                            # Payload DATA field
        data_bits = self._get_max_data_bits()  # Maximum data bits (adjusted for FEC repeats)
        decoded_frame = None                   # Stage 3/3 demodulation: decide frame symbols
        # Maximum length of frame binary
        maximum_bits = self.SYNCWORD_BITS + self.DATA_LEN_BITS + data_bits + self.CHECKSUM_BITS

        # DECODE IT
        if len(self._buffer) >= maximum_bits:
            decoded_frame = self._modem.decide_symbols(symbol_metrics=self._buffer[:maximum_bits],
                                                       threshold=0.0)
            # 1. Good Syncword?
            if self._validate_syncword(decoded_frame) is True:
                # 2. Good DATA_LEN?
                if self._validate_data_len(decoded_frame) is True:
                    # 3. Good DATA?
                    data = self._validate_data_field(decoded_frame=decoded_frame, exp_data=exp_data)

        # DONE
        return data

    def _validate_data_field(self, decoded_frame: bytes, exp_data: bytes | None) -> bytes | None:
        """Extract, validate, and return the DATA field using the checksum."""
        # LOCAL VARIABLES
        data_bits = b''                                  # The DATA field binary
        check_bits = b''                                 # The CHECKSUM field binary
        data = None                                      # Valid DATA field converted to ASCII
        exp_checksum = 0                                 # The CHECKSUM field as an int
        act_checksum = 0                                 # The checksum of the actual DATA field
        start = self.SYNCWORD_BITS + self.DATA_LEN_BITS  # Start slice into the decoded frame
        stop = start + (self._data_length * 8)           # Stop slice into the decoded frame

        # VALIDATE IT
        data_bits = decoded_frame[start:stop]
        if self._fec_repeat is not None:
            data_bits = decode_fec_repetition(bits=data_bits, repeats=self._fec_repeat)
        check_bits = decoded_frame[stop:stop+self.CHECKSUM_BITS]
        if exp_data is not None and self._debug:
            print(f'[RX] DATA BER: {calculate_ber(exp_data, data_bits)}')
        exp_checksum = self._bits_to_integer(check_bits)
        act_checksum = self._checksum(data_bits)
        if act_checksum != exp_checksum:
            if self._debug:
                print(f'[RX] Dropping failed checksum (exp={exp_checksum}, act={act_checksum}, '
                      f'checksum_bits={check_bits}, '
                      f'len(DATA)={len(data_bits)}, '
                      f'len(exp_data)={len(exp_data) if exp_data else None}, '
                      f'data={data_bits!r})')
            else:
                print('[RX] Dropping failed checksum')
        else:
            data = data_bits  # It's valid
            self._count_chk += 1  # [CFT] Found one!
        self._buffer = self._buffer[(self._data_length * 8) + self.CHECKSUM_BITS:]  # Advance it

        # DONE
        if data is None:
            self._reset()  # No data, so go back to searching
        return data

    def _validate_data_len(self, decoded_frame: bytes) -> bool:
        """Extract, validate, and store a frame's DATA_LEN field.

        Updates the _data_length attribute with the DATA_LEN value (if it's valid).

        Returns:
            True if valid, False otherwise.
        """
        # LOCAL VARIABLES
        valid = False                      # Is the DATA_LEN value valid?
        len_bits = b''                     # The DATA_LEN binary
        data_len = 0                       # The DATA_LEN value
        start = self.SYNCWORD_BITS         # Start slice into the decoded frame
        stop = start + self.DATA_LEN_BITS  # Stop slice into the decoded frame

        # VALIDATE IT
        len_bits = decoded_frame[start:stop]  # Pull it from the decoded frame
        data_len = self._bits_to_integer(len_bits)  # Convert DATA_LEN to int
        if data_len <= 0 or data_len > self._max_data_bytes:
            # Corrupted data length field
            self._buffer = self._buffer[1:]  # Drop it...
            self._reset()  # ...and keep on...
        else:
            valid = True
            self._count_len += 1  # [CFT] Found one!
            if self._debug:
                print('[CFT] Found DATA_LEN')
            self._data_length = data_len  # Store the value
            self._buffer = self._buffer[self.DATA_LEN_BITS:]  # Remove the DATA_LEN from buffer

        # DONE
        return valid

    def _validate_syncword(self, decoded_frame: bytes) -> bool:
        """Validate a frame's syncword, test it, and advance the buffer as appropriate.

        Returns:
            True if valid, False otherwise.
        """
        # LOCAL VARIABLES
        recv_syncword = None               # Syncword bits parsed from demod'd frame
        start = 0                          # Start slice into the decoded frame
        stop = start + self.SYNCWORD_BITS  # Stop slice into the decoded frame
        valid = False                      # Is the syncword valid?

        # VALIDATE IT
        recv_syncword = decoded_frame[start:stop]  # Pull it from the decoded frame
        # Good Syncword?
        if self._debug is True:
            print(f'[RX] SYNCWORD BER: {calculate_ber(self._syncword, recv_syncword)}')
        if recv_syncword != self._syncword:
            # Corrupt syncword?!
            self._buffer = self._buffer[1:]  # Discard the first symbol
            self._reset()  # Back to the start of the machine
        else:
            valid = True  # Everything checks out
            self._count_syn += 1  # [CFT] Found one!
            if self._debug:
                print('[CFT] Found syncword')
            self._buffer = self._buffer[self.SYNCWORD_BITS:]  # Remove the syncword from buffer

        # DONE
        return valid

    def _get_max_data_bits(self) -> int:
        """Get the maximum size of the data field, adjusted for FEC (if applicable)."""
        max_num_data_bits = self.MAX_DATA_FIELD_BYTES * 8
        if self._fec_repeat is not None:
            max_num_data_bits *= self._fec_repeat
        return max_num_data_bits

    @staticmethod
    def _bits_to_integer(bits: bytes) -> int:
        """Convert a binary ndarray to an integer."""
        return int(bits.decode('ascii'), 2)

    def _reset(self):
        """Reset the receiver to search for the next frame."""
        self._state = FrameState.SEARCHING
        self._data_length = None
# pylint: enable=too-many-instance-attributes,too-many-arguments,too-many-positional-arguments
