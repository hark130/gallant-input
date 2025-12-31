"""Defines a class to parse an Radio Data System (RDS) block."""

# Standard Imports
from typing import Final
# Third Party Imports
# Local Imports
from gallant_input.rds.block_id import BlockID
from gallant_input.rds.constants import RDS_CRC_POLY
from gallant_input.rds.exceptions import RDSIntegrityFailure
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
        self._rds_block_cwrd = None    # The RDS block checkword (AKA error correction field bits)
        self._validated = False        # Validate the internals once

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def verify_block_integrity(self) -> None:
        """Validate the RDS block provided.

        1. Validates internals
        2. Validate block ID
        3. Update block ID (only for BlockID.GUESS values)

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
        """
        # LOCAL VARIABLES
        crc = None  # Calculated CRC as an integer

        # VALIDATION
        self._validate_internals()

        # PREPARE
        self._split_rds_block()  # Split data and checkword

        # VERIFY INTEGRITY
        # 1. Calculate the CRC
        crc = self._calc_rds_crc()
        # 2. Validate Block ID

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _calc_rds_crc(self) -> int:
        """Calculates the RDS block CRC."""
        # LOCAL VARIABLES
        reg = int(self._rds_block_data.decode('utf-8'), 2)  # Data in a 16-bit register
        poly = int(RDS_CRC_POLY.decode('utf-8'), 2)         # RDS CRC polynomial as an integer

        # PREPARE
        reg <<= 10  # Append 10 zero bits (CRC width)

        # CALCULATE IT
        for bit in range(16):
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
        self._rds_block_cwrd = self._rds_block[RDS_BLOCK_DATA_LEN : \
                                               RDS_BLOCK_DATA_LEN + RDS_BLOCK_CORR_LEN]

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
        rds_cwrd_int = int(self._rds_block_cwrd.decode('ascii'), 2)  # Checkword as an integer
        offset_value = None                                          # Block ID offset value

        # INPUT VALIDATION
        validate_type(crc, 'crc', int)
        validate_type(block_id, 'block_id', BlockID)

        # VALIDATE IT
        offset_value = block_id.get_id_offset()  # bytes object


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
        # Type
        validate_type(var=self._rds_block, var_name='rds_block', var_type=bytes)
        # Length
        if len(self._rds_block) != RDS_BLOCK_LEN:
            raise ValueError(f'Invalid length of rds_block: {length} '
                             f'(must be of length {RDS_BLOCK_LEN})')
        # Content
        if not all(bin_char in b'01' for bin_char in self._rds_block):
            raise TypeError(f'Invalid binary value detected in rds_block: {self._rds_block}')
