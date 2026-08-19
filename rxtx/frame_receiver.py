"""Defines a state machine to parse frames from received samples."""

# Standard Imports
from enum import auto, Enum
# Third Party Imports
import numpy
# Local Imports
from gallant_input.synch.frame import find_frame_start


class FrameState(Enum):
    """The FrameReciver state."""
    SEARCHING = auto()
    READING_HEADER = auto()
    READING_DATA = auto()


class FrameReceiver:
    """A symbol-->frame state machine.

    Receives continuous-valued, time scynch'd, symbol metrics in chunks and parses frames.
    """

    PREAMBLE_BITS = 64
    SYNCWORD_BITS = 32
    DATA_LEN_BITS = 8
    HEADER_BITS = (PREAMBLE_BITS + SYNCWORD_BITS + DATA_LEN_BITS)
    # The DATA field is of variable length, as determined by the DATA_LEN field

    def __init__(self, modem: Modem, preamble: numpy.ndarray, syncword: bytes):
        self._modem = modem
        # Bipolar preamble symbol metrics
        self._preamble = numpy.asarray(preamble, dtype=numpy.float32)
        # Expected binary syncword
        # self._syncword = numpy.asarray(syncword, dtype=numpy.uint8)
        self._syncword = syncword
        self._state = FrameState.SEARCHING  # The state of the state machine
        # Symbols waiting to be processed
        self._buffer = numpy.empty(0, dtype=numpy.float32)
        # Once a preamble is found, these hold the partially assembled frame.
        self._frame_metrics = numpy.empty(0, dtype=numpy.float32)
        self._data_length = None  # DATA_LEN converted from binary to an integer

    def process(self, symbol_metrics: numpy.ndarray) -> list[bytes]:
        """Process a chunk of symbol metrics and return any complete frames."""
        # LOCAL VARIABLES
        datum = []  # A list of all the data fields currently found

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
                header_ready = self._read_header()
                if not header_ready:
                    break
            if self._state is FrameState.READING_DATA:
                data = self._read_data()
                if data is None:
                    break
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
                    self._buffer = self._buffer[-keep:]
            else:
                self._buffer = self._buffer[start:]  # Discard everything before the preamble
                self._state = FrameState.READING_HEADER  # Advance the machine state
                frame_found = True  # Found one!

        # DONE
        return frame_found

    def _read_header(self) -> bool:
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
            if not numpy.array_equal(received_syncword, self._syncword):
                # False preamble detection?!
                self._buffer = self._buffer[1:]  # Discard the first symbol
                self._state = FrameState.SEARCHING  # Back to the start of the machine
                keep_going = True  # Invalid header but continue searching anyway
            else:
                len_bits = header_bits[len_start:len_end]  # Extract DATA_LEN
                self._data_length = self._bits_to_integer(len_bits)  # Convert DATA_LEN to int
                # A valid header has been parsed
                self._frame_metrics = self._buffer[:self.HEADER_BITS]  # Beginning of DATA
                self._buffer = self._buffer[self.HEADER_BITS:]  # Remove the header from the buffer
                self._state = FrameState.READING_DATA  # Advance the machine state
                keep_going = True  # Header is valid

        # DONE
        return keep_going

    def _read_data(self) -> bytes | None:
        """Collect and decode the number of data bytes specified by DATA_LEN."""
        # LOCAL VARIABLES
        data = None                                 # Data read and decoded
        data_bits_required = self._data_length * 8  # The number of bits to read
        data_metrics = None                         # DATA field from the buffer
        data_bits = b''                             # Demodulated DATA

        # READ IT
        # if self._buffer.size >= data_bits_required:
        if len(self._buffer) >= data_bits_required:
            data_metrics = self._buffer[:data_bits_required]  # Get the DATA from the buffer
            data = self._modem.decide_symbols(data_metrics)  # Demodulation Stage 3-of-3
            # data = self._bits_to_bytes(data_bits)  # Translate the ndarray to a bytes obj
            self._buffer = self._buffer[data_bits_required:]  # Advance the buffer

        # DONE
        return data

    @staticmethod
    def _bits_to_integer(bits: numpy.ndarray) -> int:
        """Convert a binary ndarray to an integer."""
        # value = 0
        # for bit in bits:
        #     value = (value << 1) | int(bit)
        # return value
        return int(bits.decode('ascii'), 2)

    def _reset(self):
        """Reset the receiver to search for the next frame."""
        self._state = FrameState.SEARCHING
        self._frame_metrics = numpy.empty(0, dtype=numpy.float32)
        self._data_length = None
