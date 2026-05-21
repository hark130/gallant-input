"""Defines the ModemConfig data class for use with Modem()."""

# Standard Imports
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports
from gallant_input.validation import validate_bool, validate_pos_float_or_int


@dataclass
class ModemConfig(ABC):
    """Dataclass for use with the Modem() ctor."""

    # ATTRIBUTES
    # Public
    sample_rate: float | int  # The sample rate in samples-per-second
    symbol_rate: float | int  # The number of symbols-per-second

    # Private
    _validated: bool = field(default=False, repr=False)

    # ABSTRACT METHODS
    # In alphabetical order

    @abstractmethod
    def validate_content(self) -> None:
        """Use this method to validate the contents of the dataclass: type, content, length, format.

        Call this method first in each method/property defined in the sub-class.
        """
        # Functionality is defined in the sub-class when this method is overridden
        # Start with this code block...
        if self._validated is not True:
            # Validate the child class attributes
            self.validate_abc()  # Which will complete the validation and set _validated

    # PUBLIC METHODS
    # In alphabetical order

    def validate_abc(self) -> None:
        """Validate all attributes defined in the abstract base class (ABC) regardless."""
        validate_bool(self._validated, 'internal attribute _validated')  # Validate attr
        validate_pos_float_or_int(self.sample_rate, 'sample_rate')
        validate_pos_float_or_int(self.symbol_rate, 'symbol_rate')
        self._validated = True  # Done
