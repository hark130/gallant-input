"""Defines a class to parse a Radio Data System (RDS) group of blocks."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.rds.block import RDSBlock
from gallant_input.rds.block_id import BlockID
from gallant_input.rds.group_info import RDSGroupInfo
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN, RDS_BLOCK_LEN, RDS_GROUP_LEN
from gallant_input.rds.exceptions import (RDSBlockIDMismatch, RDSIntegrityFailure,
                                          RDSMsgGroupTypeMissing)
from gallant_input.rds.mgt.rds_msg_group_type00 import RDSMsgGroupType00
from gallant_input.validation import validate_bytes, validate_type


# pylint: disable=too-many-instance-attributes
class RDSGroup:
    """Parse a group of Radio Data System (RDS) blocks."""

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, rds_group: bytes, assume_na: bool = True) -> None:
        """RDSGroup ctor.

        TO DO: DON'T DO NOW... programmatically determine the region, North America or otherwise,
        based on the PI code.

        Args:
            rds_group: The CRC calculated from the RDS block data segment.
            assume_na: Assume the region is North America (e.g., RBDS vs RDS PTY codes).
        """
        self._murica = assume_na     # MURICA!
        self._rds_group = rds_group  # The RDS block
        self._rds_block_a = None     # The RDS group's RDSBlock Block A object
        self._rds_block_b = None     # The RDS group's RDSBlock Block B object
        self._rds_block_c = None     # The RDS group's RDSBlock Block C or C' object
        self._rds_block_d = None     # The RDS group's RDSBlock Block D object
        self._validated = False      # Validate the internals once
        self._verified = False       # Verify the group integrity once
        self._group_info = None      # RDSGroupInfo dataclass object

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def get_group_info(self) -> RDSGroupInfo:
        """Fetch all of the RDS group information from a validated RDS group.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # VALIDATION
        self.verify_group_integrity()

        # DONE
        return self._group_info

    def get_msg_group00(self) -> RDSMsgGroupType00:
        """Extract the Message Group Type 00 information from this RDS Group.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            RDSMsgGroupTypeMissing: This RDS group does not contain Group Type 00.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # LOCAL VARIABLES
        group_info = None  # RDS group's information
        mgt00 = None       # RDSMsgGroupType00()

        # VALIDATION
        self.verify_group_integrity()
        group_info = self.get_group_info()
        if group_info.group_type != 0x0:
            raise RDSMsgGroupTypeMissing(f'This group type is {group_info.group_type}, not 0')

        # GET IT
        mgt00 = RDSMsgGroupType00(
                msg_ver=group_info.msg_ver,
                di=self._rds_block_b.get_block_data()[13],
                char_seg=self._rds_block_b.get_block_data()[14:15],
                block3_data=self._rds_block_c.get_block_data()[:RDS_BLOCK_DATA_LEN-1],
                block4_data=self._rds_block_d.get_block_data()[:RDS_BLOCK_DATA_LEN-1],
            )

        # DONE
        return mgt00

    def verify_group_integrity(self, force: bool = False) -> None:
        """Validate the RDS group provided.

        Always call this method first when defining public methods.

        1. Validates internals
        2. Validate block IDs: A, B, C*, D
        3. Parse group information

        Args:
            force: [OPTIONAL] If True, validates everything all over again; Even if it's already
                been validated.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        validate_type(force, 'force', bool)
        if self._verified is False or force is True:
            # VALIDATION
            self._validate_internals()

            # PREPARE
            self._split_rds_group()  # Split the group into four blocks

            # VERIFY INTEGRITY
            try:
                self._validate_rds_group_integrity()
            except (RDSBlockIDMismatch, RDSIntegrityFailure) as err:
                raise RDSIntegrityFailure('This RDS group failed its integrity check: '
                                          f'{err}') from err
            # Parse group information
            self._parse_group_data()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _parse_group_data(self) -> None:
        """Parse the data from the group into an internal data class."""
        # LOCAL VARIABLES
        block_a_data = self._rds_block_a.get_block_data()  # Block A's data section
        block_b_data = self._rds_block_b.get_block_data()  # Block B's data section

        # PARSE IT
        self._group_info = \
            RDSGroupInfo(
                # BLOCK A
                pic=block_a_data[:RDS_BLOCK_DATA_LEN],
                # BLOCK B
                gtype=block_b_data[:4],
                msg_ver=block_b_data[4:5],
                tp=block_b_data[5:6],
                pty=block_b_data[6:11],
                dep=block_b_data[11:RDS_BLOCK_DATA_LEN]
            )

    def _split_rds_group(self) -> None:
        """Split self._rds_group into its data blocks."""
        # LOCAL VARIABLES
        rds_block_a = self._rds_group[RDS_GROUP_LEN-(4*RDS_BLOCK_LEN):
                                      RDS_GROUP_LEN-(3*RDS_BLOCK_LEN)]
        rds_block_b = self._rds_group[RDS_GROUP_LEN-(3*RDS_BLOCK_LEN):
                                      RDS_GROUP_LEN-(2*RDS_BLOCK_LEN)]
        rds_block_c = self._rds_group[RDS_GROUP_LEN-(2*RDS_BLOCK_LEN):
                                      RDS_GROUP_LEN-(1*RDS_BLOCK_LEN)]
        rds_block_d = self._rds_group[RDS_GROUP_LEN-(1*RDS_BLOCK_LEN):
                                      RDS_GROUP_LEN-(0*RDS_BLOCK_LEN)]

        # SPLIT IT
        self._rds_block_a = RDSBlock(rds_block=rds_block_a, block_id=BlockID.BLOCK_A)
        self._rds_block_b = RDSBlock(rds_block=rds_block_b, block_id=BlockID.BLOCK_B)
        self._rds_block_c = RDSBlock(rds_block=rds_block_c, block_id=BlockID.BLOCK_C_OR_CP)
        self._rds_block_d = RDSBlock(rds_block=rds_block_d, block_id=BlockID.BLOCK_D)

    def _validate_internals(self) -> None:
        """Validate the private attributes once."""
        if self._validated is False:
            # self._validated
            validate_type(var=self._validated, var_name='_validated attribute', var_type=bool)
            # self._murica
            validate_type(var=self._murica, var_name='assume_na', var_type=bool)
            # self._rds_group
            self._validate_rds_group()
            self._validated = True

    def _validate_rds_group(self) -> None:
        """Validate the ctor's arg on behalf of the class."""
        validate_bytes(validate_this=self._rds_group, param_name='rds_group',
                       exact_len=RDS_GROUP_LEN)
        # RDS group content will be validated by the respective RDSBlock objects

    def _validate_rds_group_integrity(self) -> None:
        """Validate each of the RDS group blocks in turn.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        self._rds_block_a.verify_block_integrity()
        self._rds_block_b.verify_block_integrity()
        self._rds_block_c.verify_block_integrity()
        self._rds_block_d.verify_block_integrity()
# pylint: enable=too-many-instance-attributes
