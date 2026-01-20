"""Defines a dataclass as a container for AIS payload information."""

# Standard Imports
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports
from gallant_input.ais.constants import AIS_MID_TO_NAME, AIS_PAYLOAD_MAX_SLOTS, AIS_PAYLOAD_SLOT_LEN
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.ais.exceptions import AISPayloadInvalid
from gallant_input.validation import validate_binary_bytes


@dataclass
class AISPayloadInfo:
    """Information about an AIS payload.

    See:
    https://www.navcen.uscg.gov/automatic-identification-system-overview
    """
    # In field order
    msg_type: bytes  # Message Type [6 bits]
    repeat: bytes    # Repeat Indicator [2 bits]
    mmsi: bytes      # Maritime Mobile Service Identity (MMSI) [30 bits]
    msg_bits: bytes  # Message Type specific fields [...]

    # Private Attributes
    _validated: bool = field(default=False, repr=False)

    # HUMAN-READABLE METHODS
    # In related-attribute order

    @property
    def message_type(self) -> int:
        """Translate the msg_type into an integer."""
        self.validate_data()
        return convert_bin_bytes_to_int(binary=self.msg_type)

    @property
    def mid(self) -> int:
        """The Maritime Identifier Digit (MID) of the country that issued the MMSI."""
        self.validate_data()
        return self._get_mid()

    @property
    def mid_name(self) -> str:
        """The name of the country that issued the MMSI."""
        self.validate_data()
        return AIS_MID_TO_NAME[self.mid]

    @property
    def mmsi_num(self) -> int:
        """Translate the MMSI value to an integer."""
        self.validate_data()
        return self._get_mmsi()

    @property
    def num_repeats(self) -> str:
        """The number of times this message has been repeated.

        From https://www.navcen.uscg.gov/ais-binary-broadcast-message8:
        Used by the repeater to indicate how many times a message has been repeated.
        0-3; default = 0; 3 = do not repeat any more.
        """
        self.validate_data()
        return convert_bin_bytes_to_int(binary=self.repeat)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def validate_data(self) -> None:
        """Validate the internal data.

        Always invoke this method first in public "getter" methods.

        Raises:
            AISPayloadInvalid: Data is not found, not AIS slot-aligned or contains too many slots.
            TypeError: Invalid data type.
            ValueError: Invalid value, non-binary digit found.
        """
        total_len = 0  # The total length of the AIS payload
        if not self._validated:
            validate_binary_bytes(self.msg_type, 'msg_type', 6)
            validate_binary_bytes(self.repeat, 'repeat', 2)
            validate_binary_bytes(self.mmsi, 'mmsi', 30)
            validate_binary_bytes(self.msg_bits, 'msg_bits')
            if self._get_mid() not in AIS_MID_TO_NAME:
                raise AISPayloadInvalid(f'Unable to locate MID: {self._get_mid()}')
            total_len = len(self.msg_type) + len(self.repeat) + len(self.mmsi) + len(self.msg_bits)
            if 0 != total_len % AIS_PAYLOAD_SLOT_LEN:
                raise AISPayloadInvalid('This AIS payload is not slot-aligned')
            if total_len > AIS_PAYLOAD_SLOT_LEN * AIS_PAYLOAD_MAX_SLOTS:
                raise AISPayloadInvalid('Too many slots for a valid AIS payload: '
                                        f'{int(total_len / AIS_PAYLOAD_SLOT_LEN)}')

            # DONE
            self._validated = True

    # PRIVATE METHODS
    # Methods listed in alphabetical order

    def _get_mid(self) -> int:
        """SPOT to fetch the MID during validation, avoiding unintentional recursion."""
        mmsi_int = self._get_mmsi()  # Convert the MMSI to an integer
        # Convert the integer into a leading-zero filled 9 digit number
        mmsi_str = str(f'{mmsi_int:09d}')
        # Convert the first three digits into an integer
        return int(mmsi_str[0:3])

    def _get_mmsi(self) -> int:
        """SPOT to fetch the MMSI during validation, avoiding unintentional recursion."""
        return convert_bin_bytes_to_int(binary=self.mmsi)
# pylint: enable=too-many-instance-attributes
