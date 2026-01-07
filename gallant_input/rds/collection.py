"""Collect Radio Data System (RDS) groups by Program identification codes (PI code)."""

# Standard Imports
from typing import List
# Third Party Imports
# Local Imports
from gallant_input.converters import convert_bin_bytes_to_hex_str
from gallant_input.rds.exceptions import RDSIntegrityFailure, RDSPICodeMismatch
from gallant_input.rds.group import RDSGroup
from gallant_input.rds.picode import RDSPICode
from gallant_input.validation import validate_type


class RDSCollection:
    """Store Radio Data System (RDS) groups by Program Identification code (PI code)."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self) -> None:
        """RDSCollection ctor."""
        self._picode_dict = {}   # bytes(pi_code) : RDSPICode
        self._validated = False  # Validate the internals once

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def add_bytes(self, group_bytes: bytes) -> None:
        """Add RDS group bytes to the appropriate set.

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
        """Add an RDSGroup object to the appropriate set.

        Args:
            rds_group: An RDSGroup object associated with the established PI code.

        Raises:
            RDSIntegrityFailure: The RDS block bytes provided has failed the integrity check.
            RDSPICodeMismatch: An internal PI code mismatch was detected.
            TypeError: Invalid data type.
            ValueError: Invalid value.
        """
        self._add_rds_group(rds_group=rds_group, var_name='rds_group')

    def fetch_pic_bytes(self) -> List[bytes]:
        """Fetch a list of all the PI code bytes contained in this collection."""
        self.verify_collection_integrity()
        return self._fetch_pic_bytes()

    def fetch_pic_strs(self) -> List[str]:
        """Fetch a list of all the PI codes, as hex values in strs, contained in this collection."""
        self.verify_collection_integrity()
        return [convert_bin_bytes_to_hex_str(pi_code) for pi_code in self._fetch_pic_bytes()]

    def verify_collection_integrity(self, force: bool = False) -> None:
        """Validate all RDS groups for all PI codes in the collection.

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
        """SPOT on how to add an RDSGroup object to the PI code dictionary.

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
        # LOCAL VARIABLES
        rds_group_pic = None  # The PI code of rds_group

        # VALIDATION
        self.verify_collection_integrity()
        rds_group_pic = self._fetch_internal_rds_group_picode(rds_group=rds_group,
                                                              var_name=var_name)

        # ADD IT
        if rds_group_pic not in self._picode_dict:
            self._picode_dict[rds_group_pic] = RDSPICode(pi_code=rds_group_pic)
        self._picode_dict[rds_group_pic].add_rds_group(rds_group=rds_group)

    def _fetch_internal_rds_group_picode(self, rds_group: RDSGroup, var_name: str) -> bytes:
        """Check and return an RDSGroup's PI code.

        Args:
            rds_group: The RDSGroup object to validate.
            var_name: The argument name that was the catalyst for the RDSGroup object
                (e.g., group_bytes, rds_group).

        Returns:
            The PI code of the RDSGroup as a bytes object.

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
            group_info = rds_group.get_group_info()  # Fetch the RDSGroupInfo object
            group_info.validate_data()  # Ensure its validated
            actual_pic = group_info.pic  # Get the PI code
        except RDSIntegrityFailure as err:
            raise RDSIntegrityFailure(f'This RDS group failed validation: {err}') from err

        # DONE
        return actual_pic

    def _fetch_pic_bytes(self) -> List[bytes]:
        """Fetch a list of all the PI code bytes contained in this collection."""
        return list(self._picode_dict.keys())

    def _validate_internals(self, force: bool = False) -> None:
        """Validate the private attributes once."""
        if self._validated is False or force is True:
            # self._validated
            validate_type(var=self._validated, var_name='_validated attribute', var_type=bool)
            # self._picode_dict
            validate_type(var=self._picode_dict, var_name='internal dictionary', var_type=dict)
            for pi_code, rds_pi_code_obj in self._picode_dict.items():
                rds_pi_code_obj.verify_pi_code_integrity(force=force)
                if pi_code != rds_pi_code_obj.get_pi_code():
                    raise RDSPICodeMismatch('This RDS collection detected an  mismatch '
                                            f'between the internal dictionary key "{pi_code}" and '
                                            'the PI code of the RDSPICode PI code of '
                                            f'"{rds_pi_code_obj.get_pi_code()}"')

            self._validated = True
