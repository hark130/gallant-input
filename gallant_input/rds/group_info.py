"""Defines a dataclass as a container for RDS group information."""

# Standard Imports
from dataclasses import dataclass, field
from typing import Final
# Third Party Imports
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_int
from gallant_input.rds.rbds_program_type import RBDSProgTypeCode
from gallant_input.rds.rds_program_type import RDSProgTypeCode
from gallant_input.validation import validate_binary_bytes


REGION_NA: Final[str] = 'North America'  # Default region


# pylint: disable=too-many-instance-attributes
# Of course it has more than 7 attributes.  It's a dataclass!
@dataclass
class RDSGroupInfo:
    """Information about an RDS group.

    See:
    https://en.wikipedia.org/wiki/Radio_Data_System#Baseband_coding_(Data-link_layer)
        -or-
    https://www.iz3mez.it/wp-content/library/ebook/RDS%20-%20The%20Radio%20Data%20System.pdf
        for details in the raw bytes.  Use the "getters" for human-readable/program-parseable
        values.
    """
    # In block/field order
    # Block 1
    pic: bytes      # Program Identification Code (PIC) [b15 — b0]
    # Block 2
    gtype: bytes    # Group Type Code [b15–b12]
    msg_ver: bytes  # Message Group Type [b11]
    tp: bytes       # Traffic Program Code [b10]
    pty: bytes      # Program Type [b9–b5]
    dep: bytes      # The rest of the bits are group type dependent [b4–b0]
    # General Use
    region: str = field(default=REGION_NA)  # TO DO: DON'T DO NOW... Get region from PIC

    # Private Attributes
    _validated: bool = field(default=False, repr=False)

    # HUMAN-READABLE METHODS
    # In related-attribute order

    @property
    def group_type(self) -> int:
        """Translate the gtype (Group Type Code) into an integer."""
        self.validate_data()
        return convert_bin_bytes_to_int(binary=self.gtype)

    @property
    def pi_code(self) -> str:
        """Convert the PI code bytes to a hexadecimal value in a string."""
        self.validate_data()
        return convert_bin_bytes_to_hex_str(binary=self.pic, add_prefix=True)

    @property
    def msg_group_type_a(self) -> bool:
        """Is this RDS group message group type A?."""
        self.validate_data()
        return self.msg_ver == b'0'  # If B0=0 then Message Group Type A else Type B

    @property
    def msg_group_type_b(self) -> bool:
        """Is this RDS group message group type B?."""
        self.validate_data()
        return self.msg_ver != b'0'  # If B0=0 then Message Group Type A else Type B

    @property
    def traffic_reports(self) -> bool:
        """Does this channel include periodic traffic reports?."""
        self.validate_data()
        return self.tp == b'1'

    @property
    def program_type(self) -> RBDSProgTypeCode | RDSProgTypeCode:
        """Translate the pty into a meaningful program type based on the region.

        Returns:
            An IntEnum dataclass of type determined by the established region:
            RBDSProgTypeCode for North America (AKA REGION_NA) and RDSProgTypeCode for all others.
        """
        prog_type = None  # An IntEnum of the program type, as interpreted by region
        self.validate_data()
        if self.region == REGION_NA:
            prog_type = RBDSProgTypeCode(convert_bin_bytes_to_int(binary=self.pty))
        else:
            prog_type = RDSProgTypeCode(convert_bin_bytes_to_int(binary=self.pty))
        return prog_type

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def validate_data(self) -> None:
        """Validate the internal data.

        Always invoke this method first in public "getter" methods.
        """
        if not self._validated:
            # Block 1
            validate_binary_bytes(self.pic, 'pic', 16)
            # Block 2
            validate_binary_bytes(self.gtype, 'gtype', 4)
            validate_binary_bytes(self.msg_ver, 'msg_ver', 1)
            validate_binary_bytes(self.tp, 'tp', 1)
            validate_binary_bytes(self.pty, 'pty', 5)
            validate_binary_bytes(self.dep, 'dep', 5)

            # DONE
            self._validated = True
# pylint: enable=too-many-instance-attributes
