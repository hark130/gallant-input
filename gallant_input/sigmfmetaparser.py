"""Defines the SigMFMeta class.

Open, parse, and answer questions about a sigmf-meta file.
"""

# Standard Imports
from pathlib import Path
from typing import Any
# Third Party Imports
import sigmf
# Local Imports
from gallant_input.validation import validate_path, validate_string, validate_type


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
    def get_center_freq(self, index: int = 0) -> int:
        """Fetch the center frequency of the capture at the specified index.

        Args:
            index: [OPTIONAL] The index, from the list of captures, to fetch the frequency from.

        Returns:
            The center frequency from the capture at index 0.

        Raises:
            FileNotFoundError: The meta data file is not found.
            KeyError: The object name is invalid or there's a mismatch between obj_name and key.
            TypeError: Bad data type.
            ValueError: Invalid value.
        """
        return self.get_obj_name_key_value(obj_name=sigmf.SigMFFile.CAPTURE_KEY,
                                           key=sigmf.SigMFFile.FREQUENCY_KEY, index=index)

    def get_obj_name_key_value(self, obj_name: str, key: str, index: int = 0) -> Any:
        """Fetch a key value from a SigMF metadata object.

        See https://sigmf.org/ for more information on the SigMF metadata objects.

        Args:
            obj_name: The name of the SigMF metadata object to search.  Use sigmf.SigMFFile macros
                for this argument (e.g., GLOBAL_KEY, CAPTURE_KEY, ANNOTATION_KEY).
                See sigmf.SigMFFile.VALID_KEYS.keys() for a list of actual values.
            key: The key to fetch from the specified obj_name.  Use sigmf.SigMFFile macros
                for this argument.
            index: [OPTIONAL] The index, from the list of captures, to fetch the frequency from.

        Returns:
            The value found at obj_name:key.

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
        """
        # LOCAL VARIABLES
        value = None  # The value from obj_name:key

        # SETUP
        self.load_data()

        # GET IT
        value = self._get_obj_name_key_value(obj_name=obj_name, key=key, index=index)

        # DONE
        return value

    def load_data(self) -> None:
        """Validate the meta file and load the data (if it hasn't been done already).

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
        """
        if self._meta_data is None:
            self._validate_file()
            self._load_file()

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

    def _get_obj_name_key_value(self, obj_name: str, key: str, index: int = 0) -> Any:
        """Fetch a key value from a SigMF metadata object.

        This method does not validate the data has been loaded.  Call self.load_data() first.

        Args:
            obj_name: The name of the SigMF metadata object to search.  Use sigmf.SigMFFile macros
                for this argument (e.g., GLOBAL_KEY, CAPTURE_KEY, ANNOTATION_KEY).
                See sigmf.SigMFFile.VALID_KEYS.keys() for a list of actual values.
            key: The key to fetch from the specified obj_name.  Use sigmf.SigMFFile macros
                for this argument.
            index: [Optional] Only used for obj_names that contain lists (e.g., captures)
        """
        # LOCAL VARIABLES
        key_val = None       # Key value from the obj_name dictionary

        # INPUT VALIDATION
        # obj_name && key
        self._validate_obj_name_key_pair(obj_name=obj_name, key=key)
        # index
        validate_type(var=index, var_name='index', var_type=int)
        if index < 0:
            raise TypeError(f'The "index" value is invalid: {index}')

        # GET VALUE
        match obj_name:
            # global
            case sigmf.SigMFFile.GLOBAL_KEY:
                key_val = self._meta_data.get_global_field(key)
            # captures
            case sigmf.SigMFFile.CAPTURE_KEY:
                cap_list = self._meta_data.get_captures()
                key_val = cap_list[index][key]
            # annotations
            case sigmf.SigMFFile.ANNOTATION_KEY:
                key_val = self._meta_data.get_annotations(key)
            case _:
                raise NotImplementedError(f'Object "{obj_name}" passed validation '
                                          'but is not supported')

        # DONE
        return key_val

    def _load_file(self) -> None:
        """Load the meta filename.

        This method does not validate any attributes.  Call self._validate_file() first.
        """
        self._meta_data = sigmf.sigmffile.fromfile(self._get_base_filename())

    def _validate_obj_name_key_pair(self, obj_name: str, key: str) -> None:
        """Validates a SigMF metadata object name against a key.

        Raises:
            KeyError: The obj_name name is invalid or there's a mismatch between obj_name and key.
        """
        # INPUT VALIDATION
        # Object
        self._validate_obj_name_name(obj_name=obj_name)
        # Key
        validate_string(validate_this=key, param_name='key', can_be_empty=False)

    def _validate_obj_name_name(self, obj_name: str) -> None:
        """Validates a SigMF metadata object name.

        Raises:
            KeyError: The obj_name name is invalid.
            TypeError: Bad data type.
            ValueError: Invalid value.
        """
        # INPUT VALIDATION
        validate_string(validate_this=obj_name, param_name='obj_name', can_be_empty=False)
        if obj_name not in sigmf.SigMFFile.VALID_KEYS:
            raise KeyError(f'The obj_name name "{obj_name}" is not a valid SigMF key')

    def _validate_file(self) -> None:
        """Validate the meta filename.

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
            ValueError: Invalid value.
        """
        validate_path(validate_this=self._meta_file, param_name='meta_filename', must_exist=True)
