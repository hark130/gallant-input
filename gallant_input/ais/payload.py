"""Defines the AISPayload class to parse AIS payloads."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.ais.constants import AIS_PAYLOAD_MAX_SLOTS, AIS_PAYLOAD_SLOT_LEN
from gallant_input.ais.payload_info import AISPayloadInfo
from gallant_input.validation import validate_binary_bytes, validate_type


class AISPayload:
    """Parse an AIS payload."""

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, bin_bytes: bytes) -> None:
        """AISPayload ctor.

        Args:
            bin_bytes: A bytes object containing an AIS payload in binary.
        """
        self._bin_bytes = bin_bytes  # The AIS payload
        self._payload_info = None    # The AISPayloadInfo object
        self._validated = False      # Validate the internals once

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def get_payload_info(self) -> AISPayloadInfo:
        """Fetch all of the payload information.

        Raises:
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        self.validate_integrity()
        return self._payload_info

    def validate_integrity(self, force: bool = False) -> None:
        """Validate the integrity of the attributes, once, and create the AISPayloadInfo() obj.

        Args:
            force: [OPTIONAL] If True, force the validation even if it's already been done.

        Raises:
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # INPUT VALIDATION
        validate_type(force, 'force', bool)

        # VALIDATION
        if self._validated is False or force is True:
            self._validate_bin_bytes()  # Verify everything
            self._create_payload_info()  # Parse the AISPayloadInfo() object
            self._validated = True  # Default: Don't validate it anymore

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _create_payload_info(self) -> None:
        """Create the AISPayloadInfo object."""
        self._payload_info = \
            AISPayloadInfo(
                msg_type=self._bin_bytes[0:6],
                repeat=self._bin_bytes[6:8],
                mmsi=self._bin_bytes[8:38],
                msg_bits=self._bin_bytes[38:]
            )

    def _validate_bin_bytes(self) -> None:
        """Validate the bin_bytes argument attribute on behalf of the class."""
        # LOCAL VARIABLES
        len_bin_bytes = 0  # The length of bin_bytes

        # VALIDATE IT
        validate_binary_bytes(validate_this=self._bin_bytes, param_name='bin_bytes')
        len_bin_bytes = len(self._bin_bytes)
        if 0 == len_bin_bytes:
            raise ValueError('The "bin_bytes" argument may not be empty')
        if 0 != (len_bin_bytes % AIS_PAYLOAD_SLOT_LEN):
            raise ValueError(f'The length of the "bin_bytes" argument (length: {len_bin_bytes}) '
                             'must be an AIS payload slot multiple')
        if len_bin_bytes > AIS_PAYLOAD_SLOT_LEN * AIS_PAYLOAD_MAX_SLOTS:
            raise ValueError('Too many slots for a valid AIS payload: '
                             f'{int(len_bin_bytes / AIS_PAYLOAD_SLOT_LEN)}')
