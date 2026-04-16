"""Defines a class to parse a Radio Data System (RDS) block."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.rds.block_id import BlockID
from gallant_input.rds.constants import (RDS_BLOCK_LEN, RDS_BLOCK_DATA_LEN, RDS_BLOCK_CWORD_LEN,
                                         RDS_CRC_POLY)
from gallant_input.rds.exceptions import RDSBlockIDMismatch, RDSIntegrityFailure
from gallant_input.validation import validate_bool, validate_binary_bytes, validate_type


class RDSBlock:
    """Parse a single Radio Data System (RDS) block."""

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, rds_block: bytes, block_id: BlockID) -> None:
        """RDSBlock ctor."""
        self._rds_block = rds_block    # The RDS block
        self._rds_block_id = block_id  # The RDS block ID
        self._rds_block_data = None    # The RDS block data field bits
        self._rds_block_cwrd = None    # The RDS block checkword (AKA error correction field bits)
        self._validated = False        # Validate the internals once

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def get_block_data(self) -> bytes:
        """Fetch the RDS block data from a validated RDS block.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # VALIDATION
        self.verify_block_integrity()

        # DONE
        return self._rds_block_data

    def get_block_id(self) -> BlockID:
        """Fetch the RDS block ID of a validated RDS block.

        The block ID may be updated during the integrity check (e.g., BlockID.BLOCK_C_OR_CP,
        BlockID.GUESS).

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # VALIDATION
        self.verify_block_integrity()

        # DONE
        return self._rds_block_id

    def verify_block_integrity(self, force: bool = False) -> None:
        """Validate the RDS block provided.

        Always call this method first when defining public methods.

        1. Validates internals
        2. Validate block ID
        3. Update block ID (only for BlockID.GUESS values)

        Args:
            force: [OPTIONAL] If True, validates everything all over again; Even if it's already
                been validated.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # LOCAL VARIABLES
        crc = None  # Calculated CRC as an integer

        # VALIDATION
        validate_bool(force, 'force')
        self._validate_internals(force=force)

        # PREPARE
        self._split_rds_block()  # Split data and checkword

        # VERIFY INTEGRITY
        # 1. Calculate the CRC
        crc = self._calc_rds_crc()
        # 2. Validate Block ID
        try:
            self._validate_rds_block_id(crc=crc)
        except RDSBlockIDMismatch as err:
            raise RDSIntegrityFailure(f'This RDS block failed its integrity check: {err}') from err

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _calc_rds_crc(self) -> int:
        """Calculates the RDS block CRC."""
        # LOCAL VARIABLES
        reg = convert_bin_bytes_to_int(self._rds_block_data)  # Data in a 16-bit register
        poly = convert_bin_bytes_to_int(RDS_CRC_POLY)         # RDS CRC polynomial as an integer

        # PREPARE
        reg <<= 10  # Append 10 zero bits (CRC width)

        # CALCULATE IT
        for _ in range(16):
            # Check MSB (bit 25)
            if reg & (1 << 25):
                reg ^= poly << 15
            reg <<= 1
        # Extract 10-bit remainder
        crc = (reg >> 16) & 0x3FF

        # DONE
        return crc

    def _split_rds_block(self) -> None:
        """Split self._rds_block into its data and error correction fields."""
        self._rds_block_data = self._rds_block[:RDS_BLOCK_DATA_LEN]
        self._rds_block_cwrd = self._rds_block[RDS_BLOCK_DATA_LEN:
                                               RDS_BLOCK_DATA_LEN + RDS_BLOCK_CWORD_LEN]

    def _validate_block_id(self, crc: int, block_id: BlockID) -> None:
        """Validates a BlockID against the CRC and the checkword.

        Args:
            crc: The CRC calculated from the RDS block data segment.
            block_id: Assumed valid and discrete block_id (e.g., A, B, C, C', D).

        Raises:
            RDSBlockIDMismatch: The checkword does not match the CRC xor BlockID offset.
            TypeError: Invalid data type.
            ValueError: Invalid value (e.g., this BlockID does not represent a discrete
                RDS Block ID).
        """
        # LOCAL VARIABLES
        offset_int = None                                          # Block ID Offset bytes as an int
        cwrd_int = convert_bin_bytes_to_int(self._rds_block_cwrd)  # Checkword as an int

        # INPUT VALIDATION
        validate_type(crc, 'crc', int)
        validate_type(block_id, 'block_id', BlockID)

        # VALIDATE IT
        offset_int = convert_bin_bytes_to_int(block_id.get_id_offset())
        if crc ^ offset_int != cwrd_int:
            raise RDSBlockIDMismatch(f'This block is not a {block_id.name} block')

# pylint: disable=too-many-branches
# The match statement was added in Python 3.10:
#   https://docs.python.org/3/reference/compound_stmts.html#match
# Inspiration:
#   https://docs.python.org/3/tutorial/controlflow.html#match-statements
    def _validate_rds_block_id(self, crc: int) -> None:
        """Validates the _rds_block_id attribute against the CRC.

        Handles all(?) BlockID enum values dynamically.

        Args:
            crc: The CRC calculated from the RDS block data segment.

        Raises:
            RDSBlockIDMismatch: The block ID does not match.
            NotImplementedError: Unsupported BlockID enum value.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # LOCAL VARIABLES
        valid_c_ids = [BlockID.BLOCK_C, BlockID.BLOCK_C_PRIME]                         # C and C'
        valid_ids = [BlockID.BLOCK_A, BlockID.BLOCK_B, BlockID.BLOCK_D] + valid_c_ids  # All
        valid = False                                                                  # Valid ID

        # VALIDATION

        # VALIDATE IT
        match self._rds_block_id:
            case BlockID.BLOCK_A:
                self._validate_block_id(crc=crc, block_id=self._rds_block_id)
                valid = True
            case BlockID.BLOCK_B:
                self._validate_block_id(crc=crc, block_id=self._rds_block_id)
                valid = True
            case BlockID.BLOCK_C:
                self._validate_block_id(crc=crc, block_id=self._rds_block_id)
                valid = True
            case BlockID.BLOCK_C_PRIME:
                self._validate_block_id(crc=crc, block_id=self._rds_block_id)
                valid = True
            case BlockID.BLOCK_D:
                self._validate_block_id(crc=crc, block_id=self._rds_block_id)
                valid = True
            case BlockID.BLOCK_C_OR_CP:
                for valid_c_id in valid_c_ids:
                    try:
                        self._validate_block_id(crc=crc, block_id=valid_c_id)
                    except RDSBlockIDMismatch:
                        pass  # Keep looking
                    else:
                        self._rds_block_id = valid_c_id  # Update the BlockID
                        valid = True
                        break  # Found a valid one so stop looking
                if not valid:
                    raise RDSBlockIDMismatch("Unable to match a valid C or C' Block ID")
            case BlockID.BLOCK_E:
                raise NotImplementedError('No support for Block E')
            case BlockID.UNKNOWN:
                raise RDSBlockIDMismatch("Will not match an UNKNOWN Block ID")
            case BlockID.GUESS:
                for valid_id in valid_ids:
                    try:
                        self._validate_block_id(crc=crc, block_id=valid_id)
                    except RDSBlockIDMismatch:
                        pass  # Keep looking
                    else:
                        self._rds_block_id = valid_id  # Update the BlockID
                        valid = True
                        break  # Found a valid one so stop looking
                if not valid:
                    raise RDSBlockIDMismatch('Unable to match a valid Block ID')
            case _:
                raise NotImplementedError(f'Unsupported BlockID value: {self._rds_block_id}')
# pylint: enable=too-many-branches

    def _validate_internals(self, force: bool = False) -> None:
        """Validate the private attributes once.

        Args:
            force: [OPTIONAL] If True, validates everything all over again; Even if it's already
                been validated.
        """
        if self._validated is False or force is True:
            # self._validated
            validate_bool(self._validated, '_validated attribute')
            # self._rds_block
            self._validate_rds_block()
            # self._rds_block_id
            validate_type(var=self._rds_block_id, var_name='block_id', var_type=BlockID)
            self._validated = True

    def _validate_rds_block(self) -> None:
        """Validate the ctor's arg on behalf of the class."""
        # Type, length, and content
        validate_binary_bytes(validate_this=self._rds_block, param_name='rds_block',
                              exact_len=RDS_BLOCK_LEN)
