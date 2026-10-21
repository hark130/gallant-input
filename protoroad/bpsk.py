"""BPSK implementation."""

# Standard Imports
# Third Party Imports
import numpy as np
# Local Imports
from protoroad.signals import upsample


class BPSK():
    """Modulate and demodulate BPSK digital signals."""

    def __init__(self, mapping: dict[int, complex], samples_per_symbol: int,
                 symbol_rate: float | int):
        """Class ctor."""
        self._bits_per_symb = 1                        # Set bits per symbol
        self._mapping = mapping                        # Constellation diagram
        self._sps = samples_per_symbol                 # Samples-per-symbol
        self._symb_rate = symbol_rate                  # Symbol rate
        self._samp_rate = self._sps * self._symb_rate  # Calculated sample rate
        self._values = np.array(list(mapping.keys()), dtype=np.int64)
        self._points = np.array(list(mapping.values()), dtype=np.complex64)

    def demap(self, values: np.ndarray) -> np.ndarray:
        """Symbol values --> bits, MSB first."""
        shifts = np.arange(self._bits_per_symb - 1, -1, -1)
        return ((values[:, None] >> shifts) & 1).astype(np.uint8).ravel()

    def demodulate(self, symbols: np.ndarray) -> np.ndarray:
        """Demodulate 1 sample-per-symbol to an np.ndarray of uint8 binary values."""
        return self.demap(self.detect(symbols))

    def detect(self, symbols: np.ndarray) -> np.ndarray:
        """Minimum-distance decision: nearest constellation point --> symbol value."""
        dist_sqrd = np.abs(symbols[:, None] - self._points[None, :])**2  # Squared distances
        return self._values[np.argmin(dist_sqrd, axis=1)]

    def modulate(self, binary: bytes) -> np.ndarray:
        """Modulate binary."""
        # LOCAL VARIABLES
        array = None       # Numpy array of ASCII bytes from bin_bytes
        bit_stream = None  # Numpy array of bits from array
        pad = 0            # Number of zeros to bad the converted binary with
        symbols = None     # Padded binary mapped to symbols in an np.ndarray

        # INPUT VALIDATION
        # CFT!?!

        # MODULATE IT
        # Convert it
        array = np.frombuffer(binary, dtype=np.uint8)
        bit_stream = (array - ord("0")).astype(np.uint8)
        # Pad it?
        pad = (-len(bit_stream)) % self._bits_per_symb
        if pad:
            bit_stream = np.concatenate([bit_stream, np.zeros(pad, dtype=np.uint8)])
        # Reshape
        grouped = bit_stream.reshape(-1, self._bits_per_symb)
        # Convert bits to integers
        ints = grouped.dot(1 << np.arange(self._bits_per_symb)[::-1])
        # Map to symbols
        symbols = np.array([self._mapping[i] for i in ints])
        # Upsample the symbols
        samples = upsample(symbols, self._sps, zero_stuff=True)

        # DONE
        return samples
