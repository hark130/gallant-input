"""Defines the RDSMsgGroupType02() dataclass."""

# Standard Imports
from dataclasses import dataclass
# Third Party Imports
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN
from gallant_input.rds.mgt.rds_msg_group_type import RDSMsgGroupType
from gallant_input.validation import validate_binary_bytes, validate_bool


# pylint: disable=duplicate-code
@dataclass(kw_only=True)  # Avoid linter false-negatives (e.g., Pylint's unexpected-keyword-arg)
class RDSMsgGroupType02(RDSMsgGroupType):
    """RDS message group type 02 dataclass.

    Group Type 2A: RadioText only
    Group Type 2B: RadioText only

    The RT feature is primarily designed for the broadcaster to transmit text messages
    of up to 64 characters at a time, for display by the fixed-location home
    receivers.

    Arguments:
        msg_ver: The message group type version found in Block B [b11], as binary bytes.
        char_seg: The character segment from Block B's data section [b3–b0]
        block3_data: The data segment from block 3 [b15 — b0]
        block4_data: The data segment from block 4 [b15 — b0]
    """

    # Public Attributes
    # See RDSMsgGroupType() for inherited attributes
    char_seg: bytes     # The Block 2 character segment
    block3_data: bytes  # The data segment from block 3
    block4_data: bytes  # The data segment from block 4

    # CORE METHODS
    # In alphabetical order

    def validate_content(self) -> None:
        """Validate the contents of the dataclass: type, content, length, format."""
        if self._validated is not True:
            validate_bool(self._validated, 'internal attribute _validated')
            validate_binary_bytes(self.msg_ver, 'msg_ver', 1)
            validate_binary_bytes(self.char_seg, 'char_seg', 4)
            validate_binary_bytes(self.block3_data, 'block3_data', 16)
            validate_binary_bytes(self.block4_data, 'block4_data', 16)
            self._validated = True

    # HUMAN-READABLE METHODS
    # See RDSMsgGroupType() for inherited methods
    # In alphabetical order

    @property
    def char_a(self) -> str:
        """The first character (A) in the radio text segment contained in this group.

        Group Type 2B only uses Block 4 to transmit characters so this method will return an
        empty string if self.msg_group_type_b is True.
        """
        character = ''  # The character parsed from this group
        self.validate_content()
        if self.msg_group_type_a is True:
            character = chr(
                convert_bin_bytes_to_int(self.block3_data[0:int(RDS_BLOCK_DATA_LEN/2)]))
        return character

    @property
    def char_b(self) -> str:
        """The second character (B) in the radio text segment contained in this group.

        Group Type 2B only uses Block 4 to transmit characters so this method will return an
        empty string if self.msg_group_type_b is True.
        """
        character = ''  # The character parsed from this group
        self.validate_content()
        if self.msg_group_type_a is True:
            character = chr(convert_bin_bytes_to_int(self.block3_data[int(RDS_BLOCK_DATA_LEN/2):
                                                                      RDS_BLOCK_DATA_LEN]))
        return character

    @property
    def char_c(self) -> str:
        """The third character (C) in the radio text segment contained in this group."""
        self.validate_content()
        return chr(convert_bin_bytes_to_int(self.block4_data[0:int(RDS_BLOCK_DATA_LEN/2)]))

    @property
    def char_d(self) -> str:
        """The fourth character (D) in the radio text segment contained in this group."""
        self.validate_content()
        return chr(convert_bin_bytes_to_int(self.block4_data[int(RDS_BLOCK_DATA_LEN/2):
                                                             RDS_BLOCK_DATA_LEN]))

    @property
    def offset(self) -> int:
        """Translate the character segment into a valid integer offset.

        The radio text is sent progressively over multiple groups.  The offset determines the
        order of assembly.
        """
        self.validate_content()
        return convert_bin_bytes_to_int(binary=self.char_seg)

    @property
    def radio_text_chunk(self) -> str:
        """The radio text characters (A? & B? & C & D) defined in this group.

        Use the group's offset values to help reassemble the full station name.
        """
        self.validate_content()
        return self.char_a + self.char_b + self.char_c + self.char_d
# pylint: enable=duplicate-code
