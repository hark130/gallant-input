"""Modify signals."""

# Standard Imports
import sys
# Third Party Imports
import numpy as np
# Local Imports


def create_rrc_taps(sps: int, span: int, alpha: float) -> np.ndarray:
    """Root-raised-cosine FIR taps, unit energy.

    Total taps = span * sps + 1, always odd.

    Args:
        sps: Samples per symbol.
        span: Filter length in symbols.
        alpha: roll-off / excess bandwidth (0 < alpha <= 1).
    """
    num_taps = span * sps + 1                             # Number of taps
    t = (np.arange(num_taps) - (num_taps - 1) / 2) / sps  # Time in symbol periods, centered on 0
    h = np.empty(num_taps)

    # Special case 1: t == 0
    at_zero = np.isclose(t, 0.0)
    h[at_zero] = 1.0 - alpha + 4.0 * alpha / np.pi

    # Special case 2: t == ±1/(4*alpha) (denominator goes to zero)
    at_sing = np.isclose(np.abs(t), 1.0 / (4.0 * alpha))
    h[at_sing] = (alpha / np.sqrt(2)) * (
        (1 + 2 / np.pi) * np.sin(np.pi / (4 * alpha))
        + (1 - 2 / np.pi) * np.cos(np.pi / (4 * alpha))
    )

    # General case
    g = ~(at_zero | at_sing)
    tg = t[g]
    h[g] = (np.sin(np.pi * tg * (1 - alpha)) + 4 * alpha * tg * np.cos(np.pi * tg * (1 + alpha))) \
           / (np.pi * tg * (1 - (4 * alpha * tg) ** 2))

    # DONE
    return h / np.sqrt(np.sum(h ** 2))  # Unit energy --> TX + RX peak = 1


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
