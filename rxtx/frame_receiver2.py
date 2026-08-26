"""Defines a state machine to parse validated frames from received samples."""

# Standard Imports
from enum import auto, Enum
# Third Party Imports
import numpy
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.modem.calc import calculate_ber
from gallant_input.synch.frame import find_frame_start
from rxtx.utilities import decode_fec_repetition


class FrameState(Enum):
    """The FrameReciver state."""
    SEARCHING = auto()
    READING_HEADER = auto()
    READING_DATA = auto()


class FrameReceiver2:
    """A symbol-->frame state machine.

    Receives continuous-valued, time scynch'd, symbol metrics in chunks, parses frames,
    and verifies data integrity.
    """

    PREAMBLE_BITS = 64
    SYNCWORD_BITS = 32
    DATA_LEN_BITS = 8
    HEADER_BITS = (PREAMBLE_BITS + SYNCWORD_BITS + DATA_LEN_BITS)
    CHECKSUM_BITS = 8
    # The DATA field is of variable length, as determined by the DATA_LEN field

    def __init__(self, modem: Modem, preamble: numpy.ndarray, syncword: bytes,
                 checksum: Callable[[bytes], int], fec_repeat: int | None,
                 max_data_bytes: int = 32):
        self._modem = modem
        # Bipolar preamble symbol metrics
        self._preamble = numpy.asarray(preamble, dtype=numpy.float32)
        # Expected binary syncword
        # self._syncword = numpy.asarray(syncword, dtype=numpy.uint8)
        self._syncword = syncword
        self._checksum = checksum  # Checksum generating function
        self._state = FrameState.SEARCHING  # The state of the state machine
        # Symbols waiting to be processed
        self._buffer = numpy.empty(0, dtype=numpy.float32)
        # Once a preamble is found, these hold the partially assembled frame.
        self._frame_metrics = numpy.empty(0, dtype=numpy.float32)
        self._data_length = None  # DATA_LEN converted from binary to an integer
        self._fec_repeat = fec_repeat  # Forward Error Correction value
        self._max_data_bytes = max_data_bytes  # Maximum size of the DATA field in bytes

    def process(self, symbol_metrics: numpy.ndarray, exp_data: bytes | None = None) -> list[bytes]:
        """Process a chunk of symbol metrics and return any complete frames.

        Args:
            symbol_metrics: One recovered symbol metric for each transmitted symbol.
            exp_data: [OPTIONAL] Controls 'debug' mode.  If defined, bit error rates (BERs) will
                be calculated and printed for the syncwords and data based on the expected data
                provided.
        """
        # LOCAL VARIABLES
        datum = []                    # A list of all the data fields currently found
        debug = exp_data is not None  # _read_header(debug) arg value

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
            if self._state is FrameState.READING_HEADER:
                header_ready = self._read_header(debug=debug)
                if not header_ready:
                    break
            if self._state is FrameState.READING_DATA:
                data = self._read_data(exp_data=exp_data)
                if data is None:
                    if self._state is FrameState.READING_DATA:
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
        if self._buffer.size >= self.PREAMBLE_BITS:
            start = find_frame_start(symbol_metrics=self._buffer, preamble=self._preamble)
            if start is None:
                # No preamble found...
                keep = self.PREAMBLE_BITS - 1  # ...but keep enough symbols in case it was split
                if self._buffer.size > keep:
                    self._buffer = self._buffer[-keep:]  # Keeping the last "keep" bits
            else:
                self._buffer = self._buffer[start:]  # Discard everything before the preamble
                self._state = FrameState.READING_HEADER  # Advance the machine state
                frame_found = True  # Found one!

        # DONE
        return frame_found

    def _read_header(self, debug: bool) -> bool:
        """Read and validate the syncword and data length.

        Returns:
            True if the caller should continue processing, False otherwise.
        """
        # LOCAL VARIABLES
        keep_going = False                                  # Should the caller continue processing?
        header_metrics = None                               # Header portion of the symbol metrics
        header_bits = b''                                   # Demodulated header metrics
        syncword_start = self.PREAMBLE_BITS                 # Starting index of the syncword
        syncword_end = syncword_start + self.SYNCWORD_BITS  # Ending index of the syncword
        received_syncword = None                            # Syncword sliced from the header
        len_start = syncword_end                            # Starting index of the data len
        len_end = len_start + self.DATA_LEN_BITS            # Ending index of the data len
        len_bits = None                                     # DATA_LEN portion of the header

        # VALIDATION
        if self._buffer.size >= self.HEADER_BITS:
            header_metrics = self._buffer[:self.HEADER_BITS]
            header_bits = self._modem.decide_symbols(header_metrics)
            # Validate the syncword
            received_syncword = header_bits[syncword_start:syncword_end]
            if debug is True:
                print(f'[RX] SYNCWORD BER: {calculate_ber(self._syncword, received_syncword)}')
            if not numpy.array_equal(received_syncword, self._syncword):
                # False preamble detection?!
                self._buffer = self._buffer[1:]  # Discard the first symbol
                self._state = FrameState.SEARCHING  # Back to the start of the machine
                keep_going = True  # Invalid header but continue searching anyway
            else:
                len_bits = header_bits[len_start:len_end]  # Extract DATA_LEN
                self._data_length = self._bits_to_integer(len_bits)  # Convert DATA_LEN to int
                if self._data_length == 0 or self._data_length > self._max_data_bytes:
                    # Corrupted data length field
                    self._buffer = self._buffer[1:]  # Drop it...
                    self._state = FrameState.SEARCHING  # ...and keep on...
                    keep_going = True  # ...looking
                else:
                    # A valid header has been parsed
                    self._frame_metrics = self._buffer[:self.HEADER_BITS]  # Beginning of DATA
                    self._buffer = self._buffer[self.HEADER_BITS:]  # Remove the header from the buffer
                    self._state = FrameState.READING_DATA  # Advance the machine state
                    keep_going = True  # Header is valid

        # DONE
        return keep_going

    def _read_data(self, exp_data: bytes | None) -> bytes | None:
        """Collect and decode the number of data bytes specified by DATA_LEN."""
        # LOCAL VARIABLES
        data = None                                 # Data read and decoded
        data_bits_required = self._data_length * 8  # The number of bits to read
        data_metrics = None                         # DATA field from the buffer
        data_bits = b''                             # Demodulated DATA
        checksum_bits = b''                         # The checksum field bits
        combined_metrics = None                     # "Decide symbols" on DATA + Checksum first
        combined_bits = b''                         # Decode both DATA + Checksum together
        exp_checksum: int = 0                       # Expected checksum
        act_checksum: int = 0                       # Actual checksum

        # READ IT
        if len(self._buffer) >= data_bits_required + self.CHECKSUM_BITS:
            combined_metrics = self._buffer[:data_bits_required + self.CHECKSUM_BITS]
            try:
                combined_bits = self._modem.decide_symbols(combined_metrics)  # Demod Stage 3-of-3
            except ValueError as err:
                if exp_data is not None:
                    print('FrameReceiver2()._read_data() caught an exception from the '
                          f'demodulator: {err}')
                self._reset()  # "Unstuck" the machine
            else:
                data = combined_bits[:data_bits_required]
                if self._fec_repeat is not None:
                    data = decode_fec_repetition(bits=data, repeats=self._fec_repeat)
                checksum_bits = combined_bits[data_bits_required:]
                if exp_data is not None:
                    print(f'[RX] DATA BER: {calculate_ber(exp_data, data)}')
                    # print(f'EXPECTED CHECKSUM (FROM exp_data): {self._checksum(exp_data)}')  # DEBUGGING
                self._buffer = self._buffer[data_bits_required:]  # Advance the buffer
                exp_checksum = self._bits_to_integer(checksum_bits)
                act_checksum = self._checksum(data)
                if act_checksum != exp_checksum:
                    print(f'[RX] Dropping failed checksum')
                    # print(f'[RX] Dropping failed checksum (exp={exp_checksum}, act={act_checksum}, '
                    #       f'checksum_bits={checksum_bits}, data_bits_required={data_bits_required})')  # DEBUGGING
                    print(f'[RX] Dropping failed checksum (exp={exp_checksum}, act={act_checksum}, '
                          f'checksum_bits={checksum_bits}, data_bits_required={data_bits_required}, '
                          f'len_data={len(data)}, len_exp_data={len(exp_data) if exp_data else None}, '
                          f'data={data!r})')
                    data = None
                    self._reset()  # Checksum failed so there's no chance of any remaining data
                self._buffer = self._buffer[self.CHECKSUM_BITS:]  # Advance the buffer

        # DONE
        return data

    @staticmethod
    def _bits_to_integer(bits: bytes) -> int:
        """Convert a binary ndarray to an integer."""
        return int(bits.decode('ascii'), 2)

    def _reset(self):
        """Reset the receiver to search for the next frame."""
        self._state = FrameState.SEARCHING
        self._frame_metrics = numpy.empty(0, dtype=numpy.float32)
        self._data_length = None
