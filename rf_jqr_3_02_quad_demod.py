"""RF JQR 3.02 Quadrature Demodulation implementation.

EXERCISE:
"Implement quadrature demodulation: https://wiki.gnuradio.org/index.php/Quadrature_Demod.
 It is an angle of the product of a one-sample delayed &conjugated input and the original
 undelayed input."

USAGE:
    python rf_jqr_3_02_quad_demod.py
"""

# Standard Imports
from typing import Final
import numpy
# Third Party Imports
# Local Imports
from gallant_input.codec import stringify_ndarray
from gallant_input.data_analysis import compare_streams
from gallant_input.modem.calc import (calculate_ber, calculate_sps, measure_phase_change,
                                      reshape_to_symbols)
from gallant_input.modem.fsk2 import FSK2
from gallant_input.modem.fsk2_config import FSK2Config
from test.modify import generate_bin_bytes

BAUD_RATE: Final[int] = 4800
BFSK_FREQ0: Final[float] = -1 * BAUD_RATE / 2
BFSK_FREQ1: Final[float] = 1 * BAUD_RATE / 2
BFSK_MAP: Final[dict[int, float]] = {0: BFSK_FREQ0, 1: BFSK_FREQ1}
SAMPLE_RATE: Final[int] = BAUD_RATE * 100


def compare_bin_bytes(in_bytes: bytes, out_bytes: bytes) -> None:
    """Compare binary bytes to each other and print the results."""
    if in_bytes == out_bytes:
        print(f'Quadrature demodulation success!')
    else:
        print(f'DATA BER: {calculate_ber(exp_bin=in_bytes, act_bin=out_bytes)}')
        compare_streams(stream1=in_bytes, stream2=out_bytes, show_index=True)


def demod_bfsk_signal(samples: numpy.ndarray, sps: int) -> bytes:
    """Replicates idealized BFSK demodulation utilizing quadrature demodulation."""
    dphi = do_quadrature_demod(samples=samples)
    dphi = numpy.append(dphi, dphi[-1])  # Extend the tail to avoid dropping the last symbol
    symbol_metrics = reshape_to_symbols(dphi, sps).mean(axis=1)
    bits = (symbol_metrics > 0).astype(numpy.uint8)  # Make bit decisions
    out_bytes = stringify_ndarray(bits)
    return out_bytes


def do_quadrature_demod(samples: numpy.ndarray) -> numpy.ndarray:
    """A named wrapper around the actual quadrature demodulation implementation."""
    return measure_phase_change(samples=samples)


def generate_bfsk_signal(bin_bytes: bytes):
    """Generate a BFSK signal from binary bytes."""
    # LOCAL VARIABLES
    sample_rate = SAMPLE_RATE  # Sample rate
    symbol_rate = BAUD_RATE    # Symbol rate
    freq0 = BFSK_FREQ0         # The 'off' frequency baseband deviation
    freq1 = BFSK_FREQ1         # The 'on' frequency baseband deviation
    samples = None             # Array of modulated samples
    config = FSK2Config(sample_rate=sample_rate, symbol_rate=symbol_rate, freq0=freq0, freq1=freq1)
    modem = FSK2(config=config)
    samples = modem.modulate(bin_bytes=bin_bytes)
    return samples


def main() -> None:
    """do_it()."""
    # 1. Create BFSK signal
    sps = calculate_sps(sample_rate=SAMPLE_RATE, symbol_rate=BAUD_RATE)
    in_bytes = generate_bin_bytes(1024)
    signal = generate_bfsk_signal(bin_bytes=in_bytes)
    # 2. Demodulate BFSK signal (using quadrature demod)
    out_bytes = demod_bfsk_signal(samples=signal, sps=sps)
    # 3. Verify the results
    compare_bin_bytes(in_bytes=in_bytes, out_bytes=out_bytes)


if __name__ == '__main__':
    main()
