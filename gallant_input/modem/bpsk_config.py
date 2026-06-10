"""Defines the BPSKConfig data class for use with BPSK()."""

# Standard Imports
from dataclasses import dataclass
# Third Party Imports
# Local Imports
from gallant_input.modem.modem_config import ModemConfig


@dataclass(kw_only=True)  # Avoid linter false-negatives (e.g., Pylint's unexpected-keyword-arg)
class BPSKConfig(ModemConfig):
    """Dataclass for use with the BPSK() ctor."""

    # ATTRIBUTES
    # Public

    # Private

    # ABSTRACT METHODS
    # In alphabetical order

    def validate_content(self) -> None:
        """Use this method to validate the contents of the dataclass: type, content, length, format.

        Call this method first in each method/property defined in the sub-class.
        """
        if self._validated is not True:
            # No additional validation required (yet)
            self.validate_abc()  # Which will complete the validation and set _validated

    # PUBLIC METHODS
    # In alphabetical order
