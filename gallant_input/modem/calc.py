"""Functions to calculate values on behalf of the modem sub-package."""


# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.modem.threshold_scheme import ThresholdScheme
from gallant_input.validation import (validate_ndarray, validate_pos_float_or_int,
                                      validate_pos_int, validate_type)


def calculate_sps(sample_rate: float | int, symbol_rate: float | int) -> int:
    """Calculate the samples per symbol.

    Args:
        sample_rate: The sample rate of the capture in Hz.
        symbol_rate: The number of symbols-per-second (1 / symbol time).

    Returns:
        The samples per symbol.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    validate_pos_float_or_int(sample_rate, 'sample_rate')
    validate_pos_float_or_int(symbol_rate, 'symbol_rate')
    return sample_rate // symbol_rate


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
    trimmed_samples = None  # The samples array trimmed to match symbol sizes
    symbols = None          # A multi-dimensional array split into symbol collections
    energies = None         # Array of energies

    # INPUT VALIDATION
    # Args validated by trim_samples()

    # COMPUTE IT
    trimmed_samples = trim_samples(samples, samples_per_symbol)
    symbols = trimmed_samples.reshape(-1, samples_per_symbol)
    energies = numpy.absolute(symbols).mean(axis=1)

    # DONE
    return energies


def compute_threshold(samples: numpy.ndarray, samples_per_symbol: int,
                      scheme: ThresholdScheme = ThresholdScheme.MEAN) -> float:
    """Compute the optimum threshold using the scheme indicated.

    Args:
        samples: A 1-dimensional array to use to calculate the threshold.
        samples_per_symbol: The number of samples required to represent one symbol.

    Returns:
        The calculated threshold as a float (numpy.float* values will be converted).\

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

    # DONE
    return float(threshold)  # Normalize numpy.float* values to floats


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


def trim_samples(samples: numpy.ndarray, samples_per_symbol: int) -> numpy.ndarray:
    """Trim a 1-dimension array of samples to hold a full collection of symbols.

    Args:
        samples: A 1-dimensional array to trim.
        samples_per_symbol: The number of samples required to represent one symbol.

    Returns:
        An array of the absolute mean values.

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    num_symbols = 0     # Number of complete symbols, valid or not, available in samples
    new_samples = None  # The trimmed samples

    # INPUT VALIDATION
    validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                     must_be_complex=False)
    validate_pos_int(samples_per_symbol, 'samples_per_symbol')

    # TRIM IT
    num_symbols = len(samples) // samples_per_symbol
    new_samples = samples[:num_symbols * samples_per_symbol]

    # DONE
    return new_samples


def _compute_kmeans_threshold(energies: numpy.ndarray) -> float:
    """Compute the optimum threshold using the k-means clustering."""
    raise NotImplementedError('This module has not yet implemented threshold support for '
                              'k-means clustering')
    # I'm not yet ready to add a new dependency to GAIN
    # pip install scikit-learn  # New depedency
    # from sklearn.cluster import KMeans  # Import statement
    kmeans = KMeans(n_clusters=2).fit(energies)
    centers = np.sort(kmeans.cluster_centers_.flatten())
    threshold = centers.mean()
    return float(threshold)  # Normalize numpy.float* values to floats
