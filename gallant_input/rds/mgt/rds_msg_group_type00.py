"""Defines the RDSMsgGroupType00() dataclass."""

# Standard Imports
from abc import ABC, abstractmethod
from dataclasses import dataclass
# Third Party Imports
# Local Imports
from gallant_idea.converters import convert_bin_bytes_to_int
from gallant_idea.rds.constants import RDS_BLOCK_DATA_LEN


@dataclass
class RDSMsgGroupType00(RDSMsgGroupType):
    """RDS message group type 00 dataclasse.

    Group Type 0A: Basic tuning and switching information only
    Group Type 0B: Basic tuning and switching information only

    The type 0A group—basic tuning and switching information—is a special case, designed
    to carry the fundamental components of RDS all together in a single group
    that will be transmitted frequently to convey many pieces of information to an
    RDS receiver to enable it to perform a considerable number of tuning functions.

    Arguments:
        msg_ver: The message group type version found in Block B [b11], as binary bytes.
        di: The Block 2 Decoder Identification Code [b2]
        char_seg: The character segment from Block B's data section [b1–b0]
        block3_data: The data segment from block 3 [b15 — b0]
        block4_data: The data segment from block 4 [b15 — b0]
    """

    # Public Attributes
    # See RDSMsgGroupType() for inherited attributes
    di: bytes           # The Block 2 Decoder Identification Code [b2]
    char_seg: bytes     # The Block 2 character segment
    block3_data: bytes  # The data segment from block 3
    block4_data: bytes  # The data segment from block 4

    # Private Attributes
    _validated: bool = field(default=False, repr=False)

    # CORE METHODS
    # In alphabetical order

    def validate_content(self) -> None:
        """Validate the contents of the dataclass: type, content, length, format."""
        if self._validated not True:
            validate_type(self._validated, 'internal attribute _validated', bool)
            validate_binary_bytes(self.msg_ver, 'msg_ver', 1)
            validate_binary_bytes(self.char_seg, 'char_seg', 2)
            validate_binary_bytes(self.block3_data, 'block3_data', 16)
            validate_binary_bytes(self.block4_data, 'block4_data', 16)
            self._validated = True

    # HUMAN-READABLE METHODS
    # See RDSMsgGroupType() for inherited methods
    # In alphabetical order

    @property
    def alt_freq(self) -> tuple[int, int]:
        """Parses the Alternative Frequency (AF) for version 0A messages.

        The type 0B group contains the same features as 0A except the AF feature.

        Raises:
            RDSFeatureUnavailable: If msg_group_type_b() is True.
        """
        self.validate_content()
        if self.msg_group_type_b() is True:
            raise RDSFeatureUnavailable('The alternative frequency (AF) feature is not '
                                        'available for data group type 0A')
        # The 16 bits of the Block 3 data segment holds two AFs.
        # Use The new RDS IEC 62106:1999 standard's "AF code tables" to interpret the values
        return tuple((convert_bin_bytes_to_int(block3_data[0:int(RDS_BLOCK_DATA_LEN/2)-1]),
            convert_bin_bytes_to_int(block3_data[int(RDS_BLOCK_DATA_LEN/2):RDS_BLOCK_DATA_LEN-1])))

    @property
    def char_a(self) -> str:
        """The first character (A) in the station name segment contained in this group.

        The station name is split into two characters (A & B), per group, spread across 4 groups.
        The offset helps reassemble the four two-character sets.  See station_name_chunk for more.
        """
        self.validate_content()
        return chr(convert_bin_bytes_to_int(block4_data[0:int(RDS_BLOCK_DATA_LEN/2)-1]))

    @property
    def char_b(self) -> str:
        """The second character (B) in the station name segment contained in this group.

        The station name is split into two characters (A & B), per group, spread across 4 groups.
        The offset helps reassemble the four two-character sets.  See station_name_chunk for more.
        """
        self.validate_content()
        return chr(convert_bin_bytes_to_int(
            block4_data[int(RDS_BLOCK_DATA_LEN/2):RDS_BLOCK_DATA_LEN-1]))

    @property
    def offset(self) -> int:
        """Translate the character segment into a valid integer offset.

        The station name and decoder identification code is sent progressively over 4 groups.
        The offset determines the order of assembly.
        """
        self.validate_content()
        return convert_bin_bytes_to_int(binary=self.char_seg)

    @property
    station_name_chunk(self) -> str:
        """The two station name characters (A & B) defined in this group.

        Use the group's offset values to help reassemble the full station name.

        Offset  Station Name Characters
                0   1   2   3   4   5   6   7
        0       A   B
        1               A   B
        2                       A   B
        3                               A   B
        """
        self.validate_content()
        return self.char_a + self.char_b
