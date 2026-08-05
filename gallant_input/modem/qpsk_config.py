"""Defines the QPSKConfig data class for use with QPSK()."""

# Standard Imports
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports
from gallant_input.modem.constants import QPSK_MAP
from gallant_input.modem.modem_config import ModemConfig
from gallant_input.synch.costas_loop import CostasLoop
from gallant_input.validation import validate_pos_int, validate_type, validate_mapper


@dataclass(kw_only=True)  # Avoid linter false-negatives (e.g., Pylint's unexpected-keyword-arg)
class QPSKConfig(ModemConfig):
    """Dataclass for use with the QPSK() ctor."""

    # ATTRIBUTES
    # Public

    carrier_recovery: CostasLoop | None = field(default=None)                    # Carrier recovery
    mapper: dict[int, complex] = field(default_factory=lambda: QPSK_MAP.copy())  # Bit mapping

    # Private

    _bits_per_sym = 2                                          # Bits per symbol

    # ABSTRACT METHODS
    # In alphabetical order

    def validate_content(self) -> None:
        """Use this method to validate the contents of the dataclass: type, content, length, format.

        Call this method first in each method/property defined in the sub-class.
        """
        if self._validated is not True:
            self.validate_qpsk()  # Validate the QPSK-specific data
            self.validate_abc()  # Which will complete the validation and set _validated

    def validate_qpsk(self) -> None:
        """Validate all attributes defined in this child class regardless of internal status."""
        self._validate_bps()
        self._validate_carrier_recovery()
        self._validate_mapper()

    # PUBLIC METHODS
    # In alphabetical order

    # PRIVATE METHODS

    def _validate_bps(self) -> None:
        """Validate the bits-per-symbol attribute."""
        validate_pos_int(self._bits_per_sym, 'internal attribute _bits_per_sym')

    def _validate_carrier_recovery(self) -> None:
        """Validate the carrier_recover attribute."""
        if self.carrier_recovery is not None:
            try:
                validate_type(self.carrier_recovery, 'carrier_recovery', CostasLoop)
            except TypeError as err:
                raise NotImplementedError('Received an unsupported "carrier recovery" object: '
                                          f'{type(self.carrier_recovery)}') from err

    def _validate_mapper(self) -> None:
        """Validate the mapper attribute."""
        self._validate_bps()
        validate_mapper(self.mapper, 'mapper', self._bits_per_sym)
