"""Defines the BPSKConfig data class for use with BPSK()."""

# Standard Imports
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.synch.costas_loop import CostasLoop
from gallant_input.validation import validate_type


@dataclass(kw_only=True)  # Avoid linter false-negatives (e.g., Pylint's unexpected-keyword-arg)
class BPSKConfig(ModemConfig):
    """Dataclass for use with the BPSK() ctor."""

    # ATTRIBUTES
    # Public

    carrier_recovery: CostasLoop | None = field(default=None)  # Carrier recovery object

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
            self.validate_bpsk()  # Validate the BPSK-specific data

    def validate_bpsk(self) -> None:
        """Validate all attributes defined in this child class regardless of internal status."""
        self._validate_carrier_recovery()

    # PUBLIC METHODS
    # In alphabetical order

    # PRIVATE METHODS

    def _validate_carrier_recovery(self) -> None:
        """Validate the carrier_recover attribute."""
        if self.carrier_recovery is not None:
            try:
                validate_type(self.carrier_recovery, 'carrier_recovery', CostasLoop)
            except TypeError:
                raise NotImplementedError('Received an unsupported "carrier recovery" object: '
                                          f'{type(self.carrier_recovery)}')
