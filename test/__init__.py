"""Defines common use variables for the entire test package."""

# Standard Imports
from pathlib import Path
from typing import Final
# Third Party Imports
from hobo.disk_operations import find_path_to_dir
# Local Imports

# Top-level directory for the repository.  Use this to for Path objects in the test package.
REPO_TL_DIR: Final[Path] = Path(find_path_to_dir(dir_to_find='gallant-input'))
