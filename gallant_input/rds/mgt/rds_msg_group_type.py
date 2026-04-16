"""Defines the RDSMsgGroupType() abstract base class (ABC) as a dataclass.

Typical Usage:
    1. Inherit from RDSMsgGroupType()
    2. Add additional attributes
    3. Override validate_content() to validate internal data
    4. [OPTIONAL] Add @property methods to format raw binary bytes into human-readable information
"""

# Standard Imports
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
# Third Party Imports
# Local Imports


@dataclass
class RDSMsgGroupType(ABC):
    """Abstract Base Class for all RDS Group Type dataclasses.

    Arguments:
        msg_ver: The message group type version found in Block B [b11], as binary bytes.
    """

    # Public Attributes
    msg_ver: bytes  # Message Group Type Version

    # Private Attributes
    _validated: bool = field(default=False, repr=False)

    # ABSTRACT METHODS
    # In alphabetical order

    @abstractmethod
    def validate_content(self) -> None:
        """Use this method to validate the contents of the dataclass: type, content, length, format.

        Call this method first in each method/property defined in the sub-class.
        """
        # Functionality is defined in the sub-class when this method is overridden
        # Start with this code block...
        # if self._validated is not True:
        #     validate_bool(self._validated, 'internal attribute _validated')  # Validate attr
        #     validate_binary_bytes(self.msg_ver, 'msg_ver', 1)  # Validate attr
        #     self._validated = True  # Done

    # HUMAN-READABLE METHODS
    # In alphabetical order

    @property
    def msg_group_type_a(self) -> bool:
        """Is this RDS group message group type A?."""
        self.validate_content()
        return self.msg_ver == b'0'  # If B0=0 then Message Group Type A else Type B

    @property
    def msg_group_type_b(self) -> bool:
        """Is this RDS group message group type B?."""
        self.validate_content()
        return self.msg_ver != b'0'  # If B0=0 then Message Group Type A else Type B
