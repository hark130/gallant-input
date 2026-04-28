"""Functions to calculate values on behalf of the modem sub-package."""


# Standard Imports
# Third Party Imports
import numpy
# Local Imports
from gallant_input.validation import validate_ndarray, validate_pos_int


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


    # INPUT VALIDATION
    validate_ndarray(array=samples, array_name='samples', can_be_empty=False, num_dim=1,
                     must_be_complex=False)


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
    num_symbols = len(samples) // self._sps
    new_samples = samples[:num_symbols * self._sps]

    # DONE
    return new_samples
