"""Defines a class to parse an Radio Data System (RDS) block."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports
from gallant_input.rds.block_id import BlockID
from gallant_input.validation import validate_type


# See: https://en.wikipedia.org/wiki/Radio_Data_System#Baseband_coding_(Data-link_layer)
RDS_BLOCK_LEN: Final[int] = 26  # The lengh, in bits, of one RDS block
RDS_BLOCK_DATA_LEN: Final[int] = 16  # The lengh, in bits, of one RDS block data field
RDS_BLOCK_CORR_LEN: Final[int] = 10  # The lengh, in bits, of one RDS block error correction field


class RDSBlock:
    """Parse a single Radio Data System (RDS) block."""

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, rds_block: bytes, block_id: BlockID) -> None:
        """RDSBlock ctor."""
        self._rds_block = rds_block    # The RDS block
        self._rds_block_id = block_id  # The RDS block ID
        self._rds_block_data = None    # The RDS block data field bits
        self._rds_block_corr = None    # The RDS block error correction field bits
        self._validated = False        # Validate the internals once

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def verify_block_integrity(self) -> None:
        """Validate the RDS block provided.

        1. Validates internals
        2. Validate block ID
        3. Update block ID (only for BlockID.GUESS values)
        """

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _split_rds_block(self) -> None:
        """Split self._rds_block into its data and error correction fields."""
        self._rds_block_data = self._rds_block[:RDS_BLOCK_DATA_LEN]
        self._rds_block_corr = self._rds_block[RDS_BLOCK_DATA_LEN : \
                                               RDS_BLOCK_DATA_LEN + RDS_BLOCK_CORR_LEN]

    def _validate_internals(self) -> None:
        """Validate the private attributes once."""
        if self._validated is False:
            # self._validated
            validate_type(var=self._validated, var_name='_validated attribute', var_type=bool)
            # self._rds_block
            self._validate_rds_block()
            # self._rds_block_id
            validate_type(var=self._rds_block_id, var_name='block_id', var_type=BlockID)
            self._validated = True

    def _validate_rds_block(self) -> None:
        """Validate the ctor's arg on behalf of the class."""
        # LOCAL VARIABLES
        length = len(self._rds_block)  # Lenght of the RDS block attribute value

        # VALIDATE IT
        validate_type(var=self._rds_block, var_name='rds_block', var_type=bytes)
        if len(self._rds_block) != RDS_BLOCK_LEN:
            raise ValueError(f'Invalid length of rds_block: {length} '
                             f'(must be of length {RDS_BLOCK_LEN})')
