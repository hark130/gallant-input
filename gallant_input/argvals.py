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
    command: str
    debug: bool
    data_file: str = field(default=None)  # SigMF data filename (.sigmf-data)
    meta_file: str = field(default=None)  # SigMF meta filename (.sigmf-meta)
