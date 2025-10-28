"""Defines the SigMFMeta class.

Open, parse, and answer questions about a sigmf-meta file.
"""

# Standard Imports
from pathlib import Path
from typing import Any
import sigmf
# Third Party Imports
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
            KeyError: The object name is invalid or there's a mismatch between object and key.
            TypeError: Bad data type.
            ValueError: Invalid value.
        """
        return self.get_object_key_value(object=sigmf.SigMFFile.CAPTURE_KEY,
                                         key=sigmf.SigMFFile.FREQUENCY_KEY, index=index)

    def get_object_key_value(self, object: str, key: str, index: int = 0) -> Any:
        """Fetch a key value from a SigMF metadata object.

        See https://sigmf.org/ for more information on the SigMF metadata objects.

        Args:
            object: The name of the SigMF metadata object to search.  Use sigmf.SigMFFile macros
                for this argument (e.g., GLOBAL_KEY, CAPTURE_KEY, ANNOTATION_KEY).
                See sigmf.SigMFFile.VALID_KEYS.keys() for a list of actual values.
            key: The key to fetch from the specified object.  Use sigmf.SigMFFile macros
                for this argument.
            index: [OPTIONAL] The index, from the list of captures, to fetch the frequency from.

        Returns:
            The value found at object:key.

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
        """
        # LOCAL VARIABLES
        value = None  # The value from object:key

        # SETUP
        self.load_data()

        # GET IT
        value = self._get_object_key_value(object=object, key=key, index=index)

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

    def _get_object_key_value(self, object: str, key: str, index: int = 0) -> Any:
        """Fetch a key value from a SigMF metadata object.

        This method does not validate the data has been loaded.  Call self.load_data() first.

        Args:
            object: The name of the SigMF metadata object to search.  Use sigmf.SigMFFile macros
                for this argument (e.g., GLOBAL_KEY, CAPTURE_KEY, ANNOTATION_KEY).
                See sigmf.SigMFFile.VALID_KEYS.keys() for a list of actual values.
            key: The key to fetch from the specified object.  Use sigmf.SigMFFile macros
                for this argument.
            index: [Optional] Only used for objects that contain lists (e.g., captures)
        """
        # LOCAL VARIABLES
        obj_contents = None  # Object contents from the metadata
        key_val = None       # Key value from the object dictionary

        # INPUT VALIDATION
        # object && key
        self._validate_object_key_pair(object=object, key=key)
        # index
        validate_type(var=index, var_name='index', var_type=int)
        if index < 0:
            raise TypeError(f'The "index" value is invalid: {index}')

        # GET VALUE
        match object:
            # global
            case sigmf.SigMFFile.GLOBAL_KEY:
                key_val = self._meta_data.get_global_info(key)
            # captures
            case sigmf.SigMFFile.CAPTURE_KEY:
                cap_list = self._meta_data.get_captures()
                key_val = cap_list[index][key]
            # annotations
            case sigmf.SigMFFile.ANNOTATION_KEY:
                key_val = self._meta_data.get_annotations(key)
            case _:
                raise NotImplementedError(f'Object "{object}" passed validation '
                                          'but is not supported')

        # DONE
        return key_val

    def _load_file(self) -> None:
        """Load the meta filename.

        This method does not validate any attributes.  Call self._validate_file() first.
        """
        self._meta_data = sigmf.sigmffile.fromfile(self._get_base_filename())

    def _validate_object_key_pair(self, object: str, key: str) -> None:
        """Validates a SigMF metadata object name against a key.
        
        Raises:
            KeyError: The object name is invalid or there's a mismatch between object and key.
        """
        # INPUT VALIDATION
        # Object
        self._validate_object_name(object=object)
        # Key
        validate_string(validate_this=key, param_name='key', can_be_empty=False)

    def _validate_object_name(self, object: str) -> None:
        """Validates a SigMF metadata object name.

        Raises:
            KeyError: The object name is invalid.
            TypeError: Bad data type.
            ValueError: Invalid value.
        """
        # INPUT VALIDATION
        validate_string(validate_this=object, param_name='object', can_be_empty=False)
        if object not in sigmf.SigMFFile.VALID_KEYS.keys():
            raise KeyError(f'The object name "{object}" is not a valid SigMF key')

    def _validate_file(self) -> None:
        """Validate the meta filename.

        Raises:
            FileNotFoundError: The meta data file is not found.
            TypeError: The meta_filename argument was not a Path object.
            ValueError: Invalid value.
        """
        validate_path(validate_this=self._meta_file, param_name='meta_filename', must_exist=True)
