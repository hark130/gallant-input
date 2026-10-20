"""Modify signals."""

# Standard Imports
import sys
# Third Party Imports
import numpy as np
# Local Imports


def upsample(symbols: np.ndarray, samples_per_symbol: int, zero_stuff: bool = True) -> np.ndarray:
    """Convert symbols into samples.

    Args:
        symbols: An array of symbols.
        samples_per_symbol: The number of samples required to represent one symbol.
        zero_stuff: [OPTIONAL] If True, will add zeros (Zero Stuffing) to symbols in the time
            domain instead of repeating the symbols (Zero-Order Hold).

    Returns:
        Each symbol in the symbols array repeated samples_per_symbol number of times.
        The zero_stuff argument will determine what's been repeated.
    """
    # LOCAL VARIABLES
    samples = None  # The symbols array, upsampled

    # INPUT VALIDATION
    # CFT!?!

    # UPSAMPLE IT
    if zero_stuff:
        samples = np.zeros(len(symbols) * samples_per_symbol, dtype=symbols.dtype)
        samples[::samples_per_symbol] = symbols
    else:
        samples = np.repeat(symbols, samples_per_symbol)

    # DONE
    return samples
