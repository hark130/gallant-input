"""Define the BlockID enum class to identify Radio Data System (RDS) blocks."""


class BlockID(IntEnum):
    """Communicate Radio Data System (RDS) block IDs among the rds sub-package."""
    BLOCK_A = 1        # Block A
    BLOCK_B = 2        # Block B
    BLOCK_C = 3        # Block C
    BLOCK_C_PRIME = 4  # Block C′
    BLOCK_D = 5        # Block D
    UNKNOWN = 6        # Undetermined block ID
    GUESS = 7          # Test all of the block IDs
