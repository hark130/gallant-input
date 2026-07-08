"""Defines the ArgVals data class used by the argument parser to communicate values."""

# Standard Imports
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports


@dataclass
class ArgVals:
    """Return value of the argument parser.

    Any attibutes with a default of None might not be used for all commands.
    """
    # MANDATORY ATTRIBUTES
    filename: str                                          # Input filename (e.g., .sigmf-data, .iq)
    debug: bool                                            # Debug mode
    symbol_rate: float | int                               # Baud rate
    # OPTIONAL ATTRIBUTES
    sample_rate: float | int | None = field(default=None)  # Sample rate
