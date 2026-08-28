"""Functions to calculate values on behalf of the modem sub-package."""


# Standard Imports
import warnings
# Third Party Imports
import numpy
# Local Imports
from gallant_input.modem.threshold_scheme import ThresholdScheme
from gallant_input.validation import (validate_binary_bytes, validate_bytes, validate_ndarray,
                                      validate_pos_float, validate_pos_float_or_int,
                                      validate_pos_int, validate_type)


def calculate_baud_rate(sample_rate: float | int, samples_per_symbol: int) -> float:
    """Calculate the baud rate (AKA symbol rate).

    Args:
        sample_rate: The sample rate of the capture in samples per second.
        samples_per_symbol: The number of samples per symbol.

    Returns:
        The baud rate (AKA symbol rate).

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    validate_pos_float_or_int(sample_rate, 'sample_rate')
    validate_pos_int(samples_per_symbol, 'samples_per_symbol')
    return sample_rate / samples_per_symbol


def calculate_ber(exp_bin: bytes, act_bin: bytes) -> float:
    """Calculate the bit error rate (BER) by comparing the expected binary to the actual binary.

    If exp_bin is longer than act_bin, each missing bit will count towards the BER.  If act_bin
    is longer than exp_bin, it will be truncated to match the len.

    Args:
        exp_bin: Expected binary.
        act_bin: Actual binary.

    Returns:
         Number of incorrect bits / total number of transmitted bits (AKA BER).

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    exp_binary = exp_bin  # Local copy of the expected binary
    act_binary = act_bin  # Local copy of the actual binary
    expected = None       # Expected binary in an numpy.ndarray
    actual = None         # Actual binary in an numpy.ndarray
    filler = b'2'         # Filler byte to guarantee an error

    # VALIDATION
    validate_binary_bytes(exp_bin, 'exp_bin', exact_len=None)
    validate_binary_bytes(act_bin, 'act_bin', exact_len=None)
    validate_bytes(filler, 'local variable "filler"', exact_len=1)  # Filler must be one byte

    # SETUP
    if len(exp_binary) > len(act_binary):
        act_binary = act_binary + filler * (len(exp_binary) - len(act_binary))  # Pad the actual bin
    elif len(act_binary) > len(exp_binary):
        act_binary = act_binary[:len(exp_binary)]  # Truncate the actual binary
    validate_bytes(act_binary, 'act_bin (modified)', exact_len=len(exp_binary))  # Final test

    # CALCULATE IT
    expected = numpy.frombuffer(exp_binary, dtype=numpy.uint8)
    actual = numpy.frombuffer(act_binary, dtype=numpy.uint8)

    # DONE
    return numpy.count_nonzero(expected != actual) / expected.size


def calculate_sps(sample_rate: float | int, symbol_rate: float | int) -> int:
    """Calculate the samples per symbol.

    Args:
        sample_rate: The sample rate of the capture in samples per second.
        symbol_rate: The number of symbols-per-second (1 / symbol time).

    Returns:
        The samples per symbol.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    validate_pos_float_or_int(sample_rate, 'sample_rate')
    validate_pos_float_or_int(symbol_rate, 'symbol_rate')
    return int(sample_rate // symbol_rate)


def compute_symbol_energies(samples: numpy.ndarray, samples_per_symbol: int) -> numpy.ndarray:
    """Calculate the average absolute value of 1-dimensional samples.

    Args:
        samples: An array to calculate the absolute mean of.
        samples_per_symbol: The number of samples required to represent one symbol.

    Returns:
        An array of the absolute mean values.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    symbols = None   # A multi-dimensional array split into symbol collections
    energies = None  # Array of energies

    # INPUT VALIDATION
    # Args validated by reshape_to_symbols()

    # COMPUTE IT
    symbols = reshape_to_symbols(samples, samples_per_symbol)
    energies = numpy.absolute(symbols).mean(axis=1)

    # DONE
    return energies


def compute_threshold(samples: numpy.ndarray, samples_per_symbol: int,
                      scheme: ThresholdScheme = ThresholdScheme.MEAN,
                      epsilon: float = 1e-6) -> float | None:
    """Compute the optimum threshold using the scheme indicated.

    Tests samples for more than one energy level using epsilong.

    Args:
        samples: A 1-dimensional array to use to calculate the threshold.
        samples_per_symbol: The number of samples required to represent one symbol.
        scheme: The intended threshold calculation scheme.
        epsilon: [OPTIONAL] Used to verify a spread in energies (two clusters).

    Returns:
        The calculated threshold as a float (numpy.float* values will be converted) or None.
        A return value of None indicates is a single cluster of samples energies and a threshold
        is meaningless.

    Raises:
        NotImplementedError: Partially implemented ThresholdScheme values.
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    threshold = 0.0  # Calculated threshold
    energies = compute_symbol_energies(samples, samples_per_symbol)  # The avg abs value of samples

    # INPUT VALIDATION
    # samples and samples_per_symbol validated by compute_symbol_energies()
    validate_type(scheme, 'scheme', ThresholdScheme)

    # COMPUTE IT
    if _test_two_clusters(energies, epsilon):
        match scheme:
            case ThresholdScheme.MIDRANGE:
                threshold = (energies.max() + energies.min()) / 2
            case ThresholdScheme.MEAN:
                threshold = energies.mean()
            case ThresholdScheme.KMEANS:
                threshold = _compute_kmeans_threshold(energies)
            case _:
                raise NotImplementedError('This function does not yet support ThresholdScheme.'
                                          f'{scheme.name}')
        threshold = float(threshold)  # Normalize numpy.float* values to floats
    else:
        threshold = None

    # DONE
    return threshold


def extract_bits_from_samples(samples: numpy.ndarray, samples_per_symbol: int,
                              threshold: float) -> numpy.ndarray:
    """Trim the samples, reshape them, avg them, and compare those values to the threshold.

    Args:
        samples: A 1-dimensional array to trim.
        samples_per_symbol: The number of samples required to represent one symbol.
        threshold: Magnitude threshold used to decide between binary results.

    Returns:
        A 1D array of uint8s representing the binary extracted from samples.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    avg_mag = None  # The samples array trimmed to match symbol sizes
    bits = None     # Bits extracted from samples

    # EXTRACT IT
    # Trim, group, and compute average magnitude
    avg_mag = compute_symbol_energies(samples, samples_per_symbol)
    # Compare values to the threshold
    bits = (avg_mag > threshold).astype(numpy.uint8)

    # DONE
    return bits


def extract_bits_from_single_cluster(samples: numpy.ndarray,
                                     samples_per_symbol: int) -> numpy.ndarray:
    """Trim the samples, reshape them, avg them, and extract bits from single cluster energies.

    Args:
        samples: A 1-dimensional array to trim.
        samples_per_symbol: The number of samples required to represent one symbol.

    Returns:
        A 1D array of uint8s representing the binary extracted from samples.

    Raises:
        RuntimeError: The samples argument appears to have more than one energy cluster.
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    avg_mag = None  # The samples array trimmed to match symbol sizes
    bits = None     # Bits extracted from samples

    # INPUT VALIDATION
    if compute_threshold(samples, samples_per_symbol) is not None:
        raise RuntimeError('These samples contain more than a single cluster')

    # EXTRACT IT
    # Trim, group, and compute average magnitude
    avg_mag = compute_symbol_energies(samples, samples_per_symbol)
    if avg_mag.mean() < 0.5:
        bits = numpy.zeros_like(avg_mag, dtype=numpy.uint8)
    else:
        bits = numpy.ones_like(avg_mag, dtype=numpy.uint8)

    # DONE
    return bits


def reshape_to_symbols(samples: numpy.ndarray, samples_per_symbol: int) -> numpy.ndarray:
    """Trim a 1-dimension array of samples and reshape it to a shape containing symbols.

    Args:
        samples: A 1-dimensional array to trim and reshape.
        samples_per_symbol: The number of samples required to represent one symbol.

    Returns:
        A trimmed array with a number of dimensions equal to samples_per_symbol.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    trimmed_samples = None  # The samples array trimmed to match symbol sizes
    symbols = None          # A multi-dimensional array split into symbol collections

    # INPUT VALIDATION
    # Args validated by trim_samples()

    # COMPUTE IT
    trimmed_samples = trim_samples(samples, samples_per_symbol)
    symbols = trimmed_samples.reshape(-1, samples_per_symbol)

    # DONE
    return symbols


def trim_samples(samples: numpy.ndarray, samples_per_symbol: int) -> numpy.ndarray:
    """Trim a 1-dimension array of samples to hold a full collection of symbols.

    Args:
        samples: A 1-dimensional array to trim.
        samples_per_symbol: The number of samples required to represent one symbol.

    Returns:
        An array of the absolute mean values.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value (e.g., Not enough samples to cover one symbol).
    """
    # LOCAL VARIABLES
    num_symbols = 0     # Number of complete symbols, valid or not, available in samples
    new_samples = None  # The trimmed samples

    # INPUT VALIDATION
    validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                     must_be_complex=False)
    validate_pos_int(samples_per_symbol, 'samples_per_symbol')
    if len(samples) < samples_per_symbol:
        raise ValueError(f'Not enough samples ({len(samples)}) for even one symbol at a '
                         f'samples per symbol of {samples_per_symbol}')

    # TRIM IT
    num_symbols = len(samples) // samples_per_symbol
    new_samples = samples[:num_symbols * samples_per_symbol]

    # DONE
    return new_samples


def _compute_kmeans_threshold(energies: numpy.ndarray) -> float:
    """Compute the optimum threshold using the k-means clustering."""
    # I'm not yet ready to add a new dependency to GAIN
    # pip install scikit-learn  # New depedency
    # from sklearn.cluster import KMeans  # Import statement
    try:
        kmeans = KMeans(n_clusters=2).fit(energies)
        centers = numpy.sort(kmeans.cluster_centers_.flatten())
        threshold = centers.mean()
        return float(threshold)  # Normalize numpy.float* values to floats
    except NameError as err:
        raise NotImplementedError('This module has not yet implemented threshold support for '
                                  'k-means clustering') from err


def _test_two_clusters(energies: numpy.ndarray, epsilon: float, ratio: float = 0.25) -> bool:
    """Test energies for more than one cluster.

    This function tests the energies twice: max/min spread vs epsilon, mean vs standard deviation.

    Args:
        energies: The array to test for clusters.
        epsilon: The yardstick to determine if there's enough distance between max and min energies.
        ratio: The coefficient of variation, a measurement of relative spread.

    Returns:
        True if there is more than one cluster.  False otherwise (e.g., All the same value).
    """
    # LOCAL VARIABLES
    two_clusters = True  # Are there two clusters or not?

    # INPUT VALIDATION
    validate_ndarray(array=energies, array_name='energies', can_be_empty=False, num_dim=1,
                     must_be_complex=False)
    validate_pos_float(epsilon, 'epsilon', abs_tol=1e-18)
    validate_pos_float(ratio, 'ratio', abs_tol=1e-18)

    # TEST IT
    two_clusters = _test_two_clusters_vs_spread(energies, epsilon)
    if not two_clusters:
        two_clusters = _test_two_clusters_vs_mean(energies, ratio)

    # DDNE
    return two_clusters


def _test_two_clusters_vs_mean(energies: numpy.ndarray, ratio: float) -> bool:
    """Test energies for more than one cluster by comparing the energy mean to std against a ratio.

    Returns:
        True if there is more than one cluster.  False otherwise (e.g., All the same value).
    """
    # LOCAL VARIABLES
    mean = energies.mean()  # Mean value of the energies
    std = energies.std()    # Standard deviation of the energy values
    two_clusters = False    # Are there two clusters or not?

    # SETUP
    warnings.filterwarnings('error', category=RuntimeWarning)  # RuntimeWarnings from some input

    # TEST IT
    try:
        if (std / mean) > ratio:
            two_clusters = True
    except (RuntimeWarning, ZeroDivisionError):
        two_clusters = False  # Mean is effectively 0 (e.g., 1e-1776)

    # DDNE
    return two_clusters


def _test_two_clusters_vs_spread(energies: numpy.ndarray, epsilon: float) -> bool:
    """Test energies for more than one cluster.

    Returns:
        True if there is more than one cluster.  False otherwise (e.g., All the same value).
    """
    # LOCAL VARIABLES
    spread = 0.0         # Spread between maximum and minimum values in energies
    two_clusters = True  # Are there two clusters or not?

    # TEST IT
    spread = energies.max() - energies.min()
    if spread < epsilon:
        two_clusters = False  # The spread is less than epsilon so there's only one cluster

    # DDNE
    return two_clusters
