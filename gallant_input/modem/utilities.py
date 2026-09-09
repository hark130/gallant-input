"""Common-use functionality for the modem sub-package."""

# Standard Imports
import math
# Third Party Imports
import numpy
# Local Imports
from gallant_input.validation import (BAD_VAL_EMPTY, validate_complex, validate_mapper,
                                      validate_pos_float_or_int)


def normalize_mapping(mapper: dict[int, complex],
                      new_avg_energy: int | float = 1) -> dict[int, complex]:
    """Normalize a constellation mapping to unit average symbol energy.

    Scales the constellation mapping so that the average symbol energy is avg_energy.

    Args:
        mapper: The bits --> symbol dictionary.
        new_avg_energy: The new average symbol energy (Es).

    Returns:
        A copy of mapper with the constellation values normalized to the specified average symbol
        energy.

    Raises:
        TypeError: Invalid data type.
        ValueError: Bad value or current average energy is zero (0).
    """
    # LOCAL VARIABLES
    new_mapper = {}      # Copy of the original dictionary
    symbols = []         # A list of symbols from the mapper
    curr_avg_energy = 0  # The current average energy of the mapper symbols (as-is)
    scale = 1.0          # The factor to scale the symbol values by
    abs_tol = 1e-5       # Let's not go crazy on floating point precision

    # INPUT VALIDATION
    validate_mapper(mapper, 'mapper', bits_per_symbol=None)
    if not mapper:
        raise ValueError(BAD_VAL_EMPTY.format('mapper'))
    validate_pos_float_or_int(new_avg_energy, 'new_avg_energy')
    for _, value in mapper.items():
        # These values *must* be complex
        validate_complex(value, 'a value in the mapper dictionary')

    # NORMALIZE IT
    symbols = list(mapper.values())
    curr_avg_energy = sum(abs(symbol) ** 2 for symbol in symbols) / len(symbols)  # E[|s|²]
    if curr_avg_energy == 0 or math.isclose(curr_avg_energy, 0, abs_tol=abs_tol):
        raise ValueError('The "mapper" constellation diagram may not have zero-average '
                         'symbol energy')  # Final validation
    if curr_avg_energy == new_avg_energy or math.isclose(curr_avg_energy, new_avg_energy,
                                                         abs_tol=abs_tol):
        new_mapper = mapper.copy()  # No need to do anything
    else:
        scale = new_avg_energy / math.sqrt(curr_avg_energy)
        new_mapper = {key: symbol * scale for key, symbol in mapper.items()}

    # DONE
    return new_mapper
