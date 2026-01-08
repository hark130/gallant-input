"""Parse Radio Data System (RDS) groups for a specific Program identification code (PI code)."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_hex_str
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN
from gallant_input.rds.exceptions import (RDSDataIncomplete, RDSIntegrityFailure,
                                          RDSMsgGroupTypeMissing, RDSPICodeMismatch)
from gallant_input.rds.group import RDSGroup
from gallant_input.validation import validate_binary_bytes, validate_list, validate_type


class RDSPICode:
    """Parse Radio Data System (RDS) groups for a specific Program Identification code (PI code)."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, pi_code: bytes) -> None:
        """RDSPICode ctor.

        Args:
            pi_code: The Program Identification code (PI code) this class is dedicated to.
                All subsequent bitstreams and/or RDSGroup objects *must* be part of this PI code.
        """
        self._pi_code = pi_code    # The dedicated PI code
        self._rds_group_objs = []  # The list of all the RDSGroup objects for this PI code
        self._validated = False    # Validate the internals once

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def add_bytes(self, group_bytes: bytes) -> None:
        """Add PI code bytes to the set.

        Args:
            group_bytes: A collection of bytes, of length RDS_GROUP_LEN, associated with the
                previously provided pi_code.

        Raises:
            RDSIntegrityFailure: The RDS block bytes provided has failed the integrity check.
            RDSPICodeMismatch: An internal PI code mismatch was detected.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        rds_group = RDSGroup(rds_group=group_bytes)
        self._add_rds_group(rds_group=rds_group, var_name='group_bytes')

    def add_rds_group(self, rds_group: RDSGroup) -> None:
        """Add an RDSGroup object to the PI code set.

        The PI code of rds_group must the same as the ctor's pi_code value.

        Args:
            rds_group: An RDSGroup object associated with the established PI code.

        Raises:
            RDSIntegrityFailure: The RDS block bytes provided has failed the integrity check.
            RDSPICodeMismatch: An internal PI code mismatch was detected.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        self._add_rds_group(rds_group=rds_group, var_name='rds_group')

    def get_pi_code(self) -> bytes:
        """Get the PI code."""
        self.verify_pi_code_integrity()
        return self._pi_code

    def get_pi_code_str(self) -> str:
        """Get the PI code as a hex string."""
        self.verify_pi_code_integrity()
        return convert_bin_bytes_to_hex_str(self.get_pi_code())

    def get_station_name(self) -> str:
        """Attempt to form the station name from Message Group Type 00s in the set.

        Returns:
            The reformed station name as a string.  The returned value will include all offsets.

        Raises:
            RDSDataIncomplete: The Message Group Types are missing one or more offsets.
            RDSMsgGroupTypeMissing: There are no Message Group Type 00s in the set.
        """
        # LOCAL VARIABLES
        station_name = ''       # The reformed station name
        offset_dict = {}        # The dictionary of offsets and their strings
        msg_groups = []         # List of Message Group Type 00s

        # VALIDATION
        self.verify_pi_code_integrity()

        # GET IT
        # List of RDSMsgGroupType00()s
        for rds_group_obj in self._rds_group_objs:
            try:
                msg_groups.append(rds_group_obj.get_msg_group00())  # EAFP
            except RDSMsgGroupTypeMissing:
                pass  # Not Message Group Type 00 so skip it
        # Validate results
        if len(msg_groups) == 0:
            raise RDSMsgGroupTypeMissing('This RDSPICode does not contain any Message Type 00s')
        # Get the offsets and station name chunks
        for msg_group in msg_groups:
            if msg_group.offset not in offset_dict:
                offset_dict[msg_group.offset] = msg_group.station_name_chunk
        # Reform station name
        try:
            station_name = offset_dict[0] + offset_dict[1] + offset_dict[2] + offset_dict[3]  # EAFP
        except KeyError as err:
            raise RDSDataIncomplete(f'Missing offeset {err.args[0]}') from err

        # DONE
        return station_name

    def verify_pi_code_integrity(self, force: bool = False) -> None:
        """Validate all RDS groups provided against the established PI code.

        Always call this method first when defining public methods.

        Args:
            force: [OPTIONAL] If True, validates everything all over again; Even if it's already
                been validated.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            RDSPICodeMismatch: An internal PI code mismatch was detected.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        validate_type(force, 'force', bool)
        self._validate_internals(force=force)

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def _add_rds_group(self, rds_group: RDSGroup, var_name: str) -> None:
        """SPOT on how to add an RDSGroup object to the PI code set.

        The PI code of rds_group must the same as the ctor's pi_code value.

        Args:
            rds_group: An RDSGroup object associated with the established PI code.
            var_name: The argument name that was the catalyst for the RDSGroup object
                (e.g., group_bytes, rds_group).

        Raises:
            RDSIntegrityFailure: The RDS block bytes provided has failed the integrity check.
            RDSPICodeMismatch: An internal PI code mismatch was detected.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # VALIDATION
        self.verify_pi_code_integrity()
        self._validate_internal_rds_group_picode(rds_group=rds_group, var_name=var_name)

        # ADD IT
        self._rds_group_objs.append(rds_group)  # It passed muster

    def _validate_internal_rds_group_picode(self, rds_group: RDSGroup, var_name: str) -> None:
        """Checks an RDSGroup's PI code against the internal attribute.

        Args:
            rds_group: The RDSGroup object to validate.
            var_name: The argument name that was the catalyst for the RDSGroup object
                (e.g., group_bytes, rds_group).

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            RDSPICodeMismatch: An internal PI code mismatch was detected.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        # LOCAL VARIABLES
        actual_pic = None  # The actual PI code parsed from rds_group

        # VALIDATE IT
        # Type
        validate_type(var=rds_group, var_name=var_name, var_type=RDSGroup)
        # Content
        # NOTE: Calling the RDSGroup.get_group_info() method will invoke the validation method
        try:
            actual_pic = rds_group.get_group_info().pic
        except RDSIntegrityFailure as err:
            raise RDSIntegrityFailure(f'This RDS PI code set has a bad RDS group: {err}') from err
        if actual_pic != self._pi_code:
            raise RDSPICodeMismatch(f'This RDS PI code set expected code "{self._pi_code}" but '
                                    f'"{actual_pic}" was parsed instead')

    def _validate_internal_rds_groups(self) -> None:
        """Validate the private list of RDSGroup objs."""
        # Type
        validate_list(validate_this=self._rds_group_objs, param_name='internal RDSGroup list',
                      can_be_empty=True)
        # Content
        for rds_group_obj in self._rds_group_objs:
            # Type, Content, and PI code
            self._validate_internal_rds_group_picode(rds_group=rds_group_obj,
                                                     var_name='internal RDSGroup object')

    def _validate_internals(self, force: bool = False) -> None:
        """Validate the private attributes once."""
        if self._validated is False or force is True:
            # self._validated
            validate_type(var=self._validated, var_name='_validated attribute', var_type=bool)
            # self._pi_code
            validate_binary_bytes(validate_this=self._pi_code, param_name='pi_code',
                                  exact_len=RDS_BLOCK_DATA_LEN)
            # self._rds_group_objs
            self._validate_internal_rds_groups()
            self._validated = True
