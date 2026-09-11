"""Defines the FSK2Config data class for use with FSK2()."""

# Standard Imports
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.validation import validate_bool, validate_int_or_float, validate_phase


@dataclass(kw_only=True)  # Avoid linter false-negatives (e.g., Pylint's unexpected-keyword-arg)
class FSK2Config(ModemConfig):
    """Dataclass for use with the FSK2() ctor."""

    # ATTRIBUTES
    # Public

    freq0: float | int                         # The 'off' frequency baseband deviation.
    freq1: float | int                         # The 'on' frequency baseband deviation.
    phase: float | None = field(default=None)  # Override the internal phase continuity.

    # Private

    _demod: bool = field(default=False)        # Only validate attrs necessary for demodulation

    # ABSTRACT METHODS
    # In alphabetical order

    def validate_content(self) -> None:
        """Use this method to validate the contents of the dataclass: type, content, length, format.

        Call this method first in each method/property defined in the sub-class.
        """
        if self._validated is not True:
            self.validate_fsk2()  # Validate the child class attributes
            self.validate_abc()   # Which will complete the validation and set _validated

    # PUBLIC METHODS
    # In alphabetical order

    def set_demod(self, demod: bool = True) -> None:
        """Set this config to demod-only.

        Args:
            demod: [OPTIONAL] Controls internal parsing/validation.  If True, internal validation
                will only validate the attributes necessary to demodulate a signal.
        """
        self._demod = demod

    def validate_fsk2(self) -> None:
        """Validate all attributes defined in this child class regardless of internal status."""
        validate_bool(self._demod, 'internal demod attribute')
        if self._demod is False:
            validate_int_or_float(self.freq0, 'freq0')  # Necessary for modulation
            validate_int_or_float(self.freq1, 'freq1')  # Necessary for modulation
            if self.phase is not None:
                validate_phase(self.phase, 'phase')  # Necessary for modulation, if defined
