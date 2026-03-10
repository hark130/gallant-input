"""Defines a dataclass as a container for AIS payload information."""

# Standard Imports
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports
from gallant_input.ais.constants import (AIS_MID_TO_NAME, AIS_MID_UNKNOWN_NUM,
                                         AIS_PAYLOAD_MAX_SLOTS, AIS_PAYLOAD_SLOT_LEN)
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.ais.exceptions import AISPayloadInvalid
from gallant_input.ais.mmsi_code_type import MMSICodeType
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
    def mmsi_code_name(self) -> str:
        """Evaluate the MMSI as a code type's nice name."""
        self.validate_data()
        return self.mmsi_code_type.nice_name

    @property
    def mmsi_code_type(self) -> MMSICodeType:
        """Evaluate the MMSI as a code type."""
        self.validate_data()
        return self._determine_mmsi_code_type()

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
        mmsi_len = 0   # The length of the MMSI string
        if not self._validated:
            validate_binary_bytes(self.msg_type, 'msg_type', 6)
            validate_binary_bytes(self.repeat, 'repeat', 2)
            validate_binary_bytes(self.mmsi, 'mmsi', 30)
            mmsi_len = len(self._get_mmsi_str())
            if mmsi_len != 9:
                raise AISPayloadInvalid(f'Invalid MMSI length of {mmsi_len}')
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

    def _determine_mmsi_code_type(self) -> MMSICodeType:
        """Determine the MMSICodeType based on the MMSI."""
        # LOCAL VARIABLES
        mmsi_str = self._get_mmsi_str()     # MMSI string
        code_type = MMSICodeType.UNDEFINED  # MMSICodeType object

        # See: https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity
        #   #The_first_digit_of_an_MMSI
        if mmsi_str.startswith('970'):
            code_type = MMSICodeType.SART  # 970yyzzzz - AIS SART (Search and Rescue Transmitter)
        elif mmsi_str.startswith('972'):
            code_type = MMSICodeType.MOB  # 972yyzzzz - MOB (Man Overboard) device
        elif mmsi_str.startswith('974'):
            code_type = MMSICodeType.EPIRB  # 974yyzzzz - Emergency Position Indicating Radio Beacon
        # See: https://www.e-navigation.nl/content/mmsi-mid-formats
        elif mmsi_str.startswith('98'):
            code_type = MMSICodeType.AUXILIARY  # 98MIDXXXX - Auxiliary craft assoc. w/ parent ship
        elif mmsi_str.startswith('99'):
            code_type = MMSICodeType.NAVIGATION  # 99MIDXXXX - Aids to Navigation
        elif mmsi_str.startswith('00'):
            code_type = MMSICodeType.COASTAL  # 00MIDXXXX - Coastal stations
        elif mmsi_str.startswith('111'):
            code_type = MMSICodeType.SAR_AIRCRAFT  # 111MIDXXX - SAR (Search and Rescue) aircraft
        elif mmsi_str.startswith('8'):
            code_type = MMSICodeType.DIVER  # 8MIDXXXXX - Diver’s radio
        elif mmsi_str.startswith('0'):
            code_type = MMSICodeType.GROUP  # 0MIDXXXXX - Group of ships
        else:
            code_type = MMSICodeType.SHIP  # MIDXXXXXX - Ship

        # DONE
        return code_type

    def _get_mid(self) -> int:
        """SPOT to fetch the MID during validation, avoiding unintentional recursion.

        For supported formats, see:
        https://www.e-navigation.nl/content/mmsi-mid-formats
            -or-
        https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity#The_first_digit_of_an_MMSI
        """
        # LOCAL VARIABLES
        code_type = self._determine_mmsi_code_type()  # MMSI code type
        mmsi_str = self._get_mmsi_str()               # MMSI string
        mid_str = ''                                  # MID string

        # PARSE IT
        # MID undefined
        if code_type in [MMSICodeType.SART, MMSICodeType.MOB, MMSICodeType.EPIRB]:
            # See: https://en.wikipedia.org/wiki/Maritime_Mobile_Service_Identity
            #   #The_first_digit_of_an_MMSI
            # 970yyzzzz - AIS SART (Search and Rescue Transmitter)
            # 972yyzzzz - MOB (Man Overboard) device
            # 974yyzzzz - EPIRB (Emergency Position Indicating Radio Beacon) AIS
            mid_str = str(AIS_MID_UNKNOWN_NUM)
        # Two digits preceding the MID
        elif code_type in [MMSICodeType.COASTAL, MMSICodeType.AUXILIARY, MMSICodeType.NAVIGATION]:
            # 00MIDXXXX - Coastal stations
            # 98MIDXXXX - Auxiliary craft associated with a parent ship
            # 99MIDXXXX - Aids to Navigation
            mid_str = mmsi_str[2:5]
        # Three digits preceding the MID
        elif code_type in [MMSICodeType.SAR_AIRCRAFT]:
            # 111MIDXXX - SAR (Search and Rescue) aircraft
            mid_str = mmsi_str[3:6]
        # One digit preceding the MID
        elif code_type in [MMSICodeType.GROUP, MMSICodeType.DIVER]:
            # 0MIDXXXXX - Group of ships; the U.S. Coast Guard, for example, is 03699999
            # 8MIDXXXXX - Diver’s radio (not used in the U.S. in 2013)
            mid_str = mmsi_str[1:4]
        # Leading MID
        elif code_type in [MMSICodeType.SHIP]:
            mid_str = mmsi_str[0:3]  # MIDXXXXXX - Ship
        else:
            mid_str = str(AIS_MID_UNKNOWN_NUM)  # In lieu of raising an exception...

        # DONE
        return int(mid_str)

    def _get_mmsi(self) -> int:
        """SPOT to fetch the MMSI during validation, avoiding unintentional recursion."""
        return convert_bin_bytes_to_int(binary=self.mmsi)

    def _get_mmsi_str(self) -> str:
        """SPOT to fetch the MMSI, as a stirng, during validation thereby avoiding recursion."""
        return str(f'{self._get_mmsi():09d}')

# pylint: enable=too-many-instance-attributes
