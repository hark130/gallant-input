"""Defines the SigMFMeta class.

Open, parse, and answer questions about a sigmf-meta file.
"""

# Standard Imports
from pathlib import Path
# Third Party Imports
from sigmf import sigmffile
# Local Imports
from gallant_input.validation import validate_path


class SigMFMetaParser:
    """Answer questions about a sigmf-meta file."""

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, meta_filename: Path) -> None:
        """SigMFMeta ctor."""
        self._meta_data = None           # The sigmf-meta data
        self._meta_file = meta_filename  # The sigmf-meta file

    # COMMON-USE METHODS
    # Methods listed in alphabetical order
    def load_data(self) -> None:
        """Validate the meta file and load the data (if it hasn't been done already).

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
        """
        if self._meta_data is None:
            self._validate_file()
            self._load_file()
            print(f'META: {self._meta_data}')  # DEBUGGING

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
    def _get_base_filename(self) -> str:
        """Dynamically fetch the base meta filename.

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
        """
        # LOCAL VARIABLES
        base_name = None  # The base filename, sans file extension, of self._meta_file

        # VALIDATION
        self._validate_file()

        # PARSE IT
        base_name = self._meta_file.with_suffix('')

        # DONE
        return base_name

    def _load_file(self) -> None:
        """Load the meta filename.

        This method does not validate any attributes.  Call self._validate_file() first.
        """
        self._meta_data = sigmffile.fromfile(self._get_base_filename())

    def _validate_file(self) -> None:
        """Validate the meta filename.

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
        """
        validate_path(validate_this=self._meta_file, param_name='meta_filename', must_exist=True)
