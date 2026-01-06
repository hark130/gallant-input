"""Parse Radio Data System (RDS) groups for a specific Program identification code (PI code)."""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN, RDS_GROUP_LEN
from gallant_input.rds.exceptions import RDSIntegrityFailure, RDSPICodeMismatch
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

    def verify_pi_code_integrity(self) -> None:
        """Validate all RDS groups provided against the established PI code.

        Always call this method first when defining public methods.

        Raises:
            RDSIntegrityFailure: The RDS block has failed its integrity check.
            RDSPICodeMismatch: An internal PI code mismatch was detected.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        self._validate_internals()


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
            raise RDSIntegrityFailure(f'This RDS PI code set detected a bad RDS group: {err}')
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
            self._validate_internal_rds_group_picode(rds_group=rds_group_obj)

    def _validate_internals(self) -> None:
        """Validate the private attributes once."""
        if self._validated is False:
            # self._validated
            validate_type(var=self._validated, var_name='_validated attribute', var_type=bool)
            # self._pi_code
            validate_binary_bytes(validate_this=self._pi_code, param_name='pi_code',
                                  exact_len=RDS_BLOCK_DATA_LEN)
            # self._rds_group_objs
            self._validate_internal_rds_groups()
            self._validated = True
