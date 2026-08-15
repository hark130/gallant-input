"""Create samples from binary data.

python -m devops.scripts.create_samples
"""


# Standard Imports
from pathlib import Path
from typing import Any
import numpy
import sys
# Third Party Imports
# Local Imports
from gallant_input.codec import convert_ascii_bin_bytes_to_bits
from gallant_input.constants import SIG_FIELD_GLOBAL_KEY, SIG_GLOB_DESCRIPTION_KEY
from gallant_input.gain_sigmf.sigmfdatatype import SigMFDataType
from gallant_input.gain_sigmf.sigmfmetabuilder import build_dataset_format, build_default_metadata
from gallant_input.io import write_samples
from gallant_input.modem.calc import calculate_baud_rate, calculate_sps
from gallant_input.modem.fsk2 import FSK2
from gallant_input.spacetime import create_rfc_3339_z_time


def build_metadata(dataset_format: str = 'cf32_le', samp_rate: int | float | None = None,
                   add_time: bool = True, center_freq: float | None = None,
                   description: str | None = None) -> dict[str:Any]:
    """Build the metadata for a SigMF file.
        dataset_format: [OPTIONAL] A non-empty string w/ a SigMF Dataset Format that conforms with
            Augmented Backus-Naur form (ABNF) rules.  Use build_dataset_format() to build this str.
            This value may not be None because it is required.
        samp_rate: [OPTIONAL] The sampling frequency in Hz.
        add_time: [OPTIONAL] If True, builds an ISO-8601 string indicating the timestamp using
            create_rfc_3339_z_time().
        center_freq: [OPTIONAL] The center frequency of the signal in Hz.
        description: [OPTIONAL] A text description of the SigMF Recording.

    Returns:
        A basic SigMF dictionary containing a global object, captures array, and an
        annotations array.
    """
    # LOCAL VARIABLES
    date_time = None  # An optional ISO-8601 string indicating the timestamp
    metadata = {}     # The SigMF metadata

    # BUILD IT
    if add_time:
        date_time = create_rfc_3339_z_time()
    metadata = build_default_metadata(dataset_format=dataset_format, samp_rate=samp_rate,
                                      date_time=date_time, center_freq=center_freq)
    if description is not None:
        metadata[SIG_FIELD_GLOBAL_KEY][SIG_GLOB_DESCRIPTION_KEY] = description

    # DONE
    return metadata


def create_filename(preamble: str, sample_rate: int | float,
                    symbol_rate: int | float, center_freq: int | float = 0) -> str:
    """Build an IQ filename string-literal based on given values.

    Uses sample rate and symbol rate to calculate the baud rate.
    TD: DDN... Convert float values to be filename friendly in a conventional way.

    Args:
        preamble: The beginning of the filename.  E.g., 'my_capture'
        center_freq: Center frequency of the sample, in hertz.
        sample_rate: The sample rate of the capture in samples per second.
        symbol_rate: The number of symbols-per-second.

    Returns:
        Effectively, f'{preamble}_c{center_freq}hz_s{sample_rate}_b{baud_rate}.iq'.
    """
    # LOCAL VARIABLES
    def_name = '{}_c{}hz_s{}_b{}.iq'                                  # Default format of the name
    samples_per_symbol = calculate_sps(sample_rate, symbol_rate)      # Samples per symbol, calc'd
    baud_rate = calculate_baud_rate(sample_rate, samples_per_symbol)  # Baud rate, calculated
    new_name = ''                                                     # New filename (from def_name)

    # CREATE IT
    new_name = def_name.format(preamble, str(center_freq), str(sample_rate), str(int(baud_rate)))

    # DONE
    return new_name


def modulate_bfsk(sample_rate: int | float, symbol_rate: int | float,
                  bin_bytes: bytes) -> numpy.ndarray:
    """Modulate binary into BFSK using the calculated baud rate to determine freq0 and freq1."""
    # LOCAL VARIABLES
    samples_per_symbol = calculate_sps(sample_rate, symbol_rate)      # Samples per symbol, calc'd
    baud_rate = calculate_baud_rate(sample_rate, samples_per_symbol)  # Baud rate, calculated
    freq0 = -(baud_rate / 2)                                          # The 'off' freq baseband dev.
    freq1 = baud_rate / 2                                             # The 'on' freq baseband dev.
    fsk2_obj = FSK2(sample_rate, symbol_rate)                         # FSK2() object
    samples = fsk2_obj.modulate(bin_bytes, freq0, freq1)              # Modulated binary

    # DONE
    return samples


def create_bfsk_input1(preamble: str = 'bfsk_mod1') -> None:
    """Build BFSK input 1 and write it to a file.

    Args:
        preamble: The beginning of the filename.  E.g., 'my_capture'
    """
    # LOCAL VARIABLES
    samp_rate = 48000      # Test case sample rate
    sym_rate = 80          # Test case symbol rate
    samples = None         # An ndarray of modulated binary to write to disk
    dataset_format = None  # SigMF metadata "global":"core:datatype" e.g., 'cf32_le'
    metadata = {}          # SigMF metadata dictionary: dict[str:Any]
    filename = None        # Path object with the output filename
    # Digital data to modulate
    bin_bytes = b'10101010'

    # BUILT IT
    samples = modulate_bfsk(samp_rate, sym_rate, bin_bytes)
    data_format = build_dataset_format(is_complex=True, data_type=SigMFDataType.FLOAT,
                                       bit_width=64, little_e=True)
    metadata = build_metadata(dataset_format=data_format, samp_rate=samp_rate,
                              center_freq=None, description=bin_bytes.decode('ascii'))
    filename = Path(create_filename(preamble, samp_rate, sym_rate))
    write_samples(filename=filename, samples=samples, sample_dtype=numpy.complex64,
                  metadata=metadata, overwrite=True)


def create_bfsk_input2(preamble: str = 'bfsk_mod2') -> None:
    """Build BFSK input 2 and write it to a file.

    Args:
        preamble: The beginning of the filename.  E.g., 'my_capture'
    """
    # LOCAL VARIABLES
    samp_rate = 57000      # Test case sample rate
    sym_rate = 2375        # Test case symbol rate
    samples = None         # An ndarray of modulated binary to write to disk
    dataset_format = None  # SigMF metadata "global":"core:datatype" e.g., 'cf32_le'
    metadata = {}          # SigMF metadata dictionary: dict[str:Any]
    filename = None        # Path object with the output filename
    # Digital data to modulate
    bin_bytes = b'0100001101100001011011100010000001111001011011110111010100100000' \
                b'0111001001100101011000010110010000100000011101000110100001101001' \
                b'0111001100111111'

    # BUILT IT
    samples = modulate_bfsk(samp_rate, sym_rate, bin_bytes)
    data_format = build_dataset_format(is_complex=True, data_type=SigMFDataType.FLOAT,
                                       bit_width=64, little_e=True)
    metadata = build_metadata(dataset_format=data_format, samp_rate=samp_rate,
                              center_freq=None, description=bin_bytes.decode('ascii'))
    filename = Path(create_filename(preamble, samp_rate, sym_rate))
    write_samples(filename=filename, samples=samples, sample_dtype=numpy.complex64,
                  metadata=metadata, overwrite=True)


def create_bfsk_input3(preamble: str = 'bfsk_mod3') -> None:
    """Build BFSK input 3 and write it to a file.

    Args:
        preamble: The beginning of the filename.  E.g., 'my_capture'
    """
    # LOCAL VARIABLES
    samp_rate = 480000     # Test case sample rate
    sym_rate = 800         # Test case symbol rate
    samples = None         # An ndarray of modulated binary to write to disk
    dataset_format = None  # SigMF metadata "global":"core:datatype" e.g., 'cf32_le'
    metadata = {}          # SigMF metadata dictionary: dict[str:Any]
    filename = None        # Path object with the output filename
    # Digital data to modulate
    bin_bytes = b'0010000000100000001000000010000001010111011010000110000101110100' \
                b'0010000001101001011100110010000001101000011000010111000001110000' \
                b'0110010101101110011010010110111001100111001111110010000100100000' \
                b'001000000010000000100000'

    # BUILT IT
    samples = modulate_bfsk(samp_rate, sym_rate, bin_bytes)
    data_format = build_dataset_format(is_complex=True, data_type=SigMFDataType.FLOAT,
                                       bit_width=64, little_e=True)
    metadata = build_metadata(dataset_format=data_format, samp_rate=samp_rate,
                              center_freq=None, description=bin_bytes.decode('ascii'))
    filename = Path(create_filename(preamble, samp_rate, sym_rate))
    write_samples(filename=filename, samples=samples, sample_dtype=numpy.complex64,
                  metadata=metadata, overwrite=True)


def main() -> int:
    """Entry-level function."""
    # LOCAL VARIABLES
    exit_code = 0  # 0 for success, 1 for error

    # CREATE SAMPLES
    try:
        create_bfsk_input1()
        create_bfsk_input2()
        create_bfsk_input3()
    except (LookupError, NotImplementedError, TypeError, ValueError) as err:
        print(f'Failed with: {repr(err)}')
        exit_code = 1  # Failed
        # raise err from err

    # DONE
    return exit_code


if __name__ == '__main__':
    sys.exit(main())
