"""Define the BlockID enum class to identify Radio Data System (RDS) blocks."""

# Standard Imports
from enum import auto, IntEnum
# Third Party Imports
# Local Imports
from gallant_input.rds.constants import (RDS_OFFSET_A, RDS_OFFSET_B, RDS_OFFSET_C,
                                         RDS_OFFSET_C_PRIME, RDS_OFFSET_D, RDS_OFFSET_E)


class BlockID(IntEnum):
    """Communicate Radio Data System (RDS) block IDs among the rds sub-package."""
    BLOCK_A = auto()        # Block A
    BLOCK_B = auto()        # Block B
    BLOCK_C = auto()        # Block C
    BLOCK_C_PRIME = auto()  # Block C′
    BLOCK_C_OR_CP = auto()  # Block C or C′
    BLOCK_D = auto()        # Block D
    BLOCK_E = auto()        # Block D
    GUESS = auto()          # Test all of the block IDs
    UNKNOWN = auto()        # Undetermined block ID

    def get_id_offset(self) -> bytes:
        """Get the offset value associated with a discrete Block ID.

        Returns:
            A bytes object with the RDS Offset binary value.

        Raises:
            ValueError: This BlockID does not represent a discrete (AKA "single") RDS Block ID.
        """
        # LOCAL VARIABLES
        offset_value = None

        # GET IT
        match self:
            case BlockID.BLOCK_A:
                offset_value = RDS_OFFSET_A
            case BlockID.BLOCK_B:
                offset_value = RDS_OFFSET_B
            case BlockID.BLOCK_C:
                offset_value = RDS_OFFSET_C
            case BlockID.BLOCK_C_PRIME:
                offset_value = RDS_OFFSET_C_PRIME
            case BlockID.BLOCK_D:
                offset_value = RDS_OFFSET_D
            case BlockID.BLOCK_E:
                offset_value = RDS_OFFSET_E
            case _:
                raise ValueError(f'The "{self.name}" BlockID has no discrete offset')

        # DONE
        return offset_value
