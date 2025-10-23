"""Defines the root GAIN Component Test Class.

Import RootCompTest for more details and usage instructions.

    Typical usage example:

    from test.comp_test.root_comp_test import RootCompTest

    class GainCompTest(RootCompTest):
        def __init__(self, *args, **kwargs) -> None:
            ...

    Environment variable usage:

    # GENERATING REPORT OUTPUT
    > export TEDIOUS_START_VERBOSE_OVERRIDE=True      # Use this to set verbosity to ALL
    > python -m test.comp_test                        # Executes all functional test cases
    > unset TEDIOUS_START_VERBOSE_OVERRIDE            # Unset it to "clean" your environment
"""

# Standard Imports
from pathlib import Path
from typing import Any, Tuple
from test.test_case_data import TestCaseData  # Standard?
import shutil
import stat
# Third Party Imports
from tediousstart.tediousfunctest import TediousFuncTest
from tediousstart.verbosity import Verbosity
from hobo.argmanager import ArgManager
from hobo.disk_operations import (calc_file_md5sum, create_dir, create_file, delete_file,
                                  delete_files, destroy_dir, list_files)
from hobo.subprocess_wrapper import execute_subprocess_cmd, get_subprocess_cmd_exit
import oschmod  # Pylint told me to put it here
# Local Imports


class RootCompTest(TediousFuncTest):
    """GAIN functional test class.

    Defines functionality needed by all of this project's functional tests.

    Available features:
        # 4. Misc.
        # Some test cases require unique functionality
        self.create_dir()    # Create a directory at "test time"
        self.create_file()   # Create a file at "test time"
        self.get_test_name() # Get the full test name, ie 'Normal_01', from test_case_data
        self.lock_file()     # Lock a file at "test time"
        self.set_dir_ro()    # Make a directory read-only at "test time"
        self.set_file_ro()   # Make a file read-only at "test time"

    Attributes:
        test_case_data:     # Stores data about the test case as a TestCaseData object
    """

    # CORE CLASS METHODS
    # Methods listed in call order
    def __init__(self, *args, **kwargs) -> None:
        """RootCompTest ctor."""
        self._arg_mngr_obj = ArgManager()  # Manage the arguments for the test author
        self._cleanup_dir_list = []        # List of directories to destroy during TearDown()
        self._cleanup_file_list = []       # List of files to delete during TearDown()
        self._locked_file_objs = []        # List of locked files (as streams returned by open())
        self._restore_perms = []           # Restore permissions for these paths
        self.test_case_data = None         # Parse the test case names for discrete snippets

        super().__init__(*args, **kwargs)

    def setUp(self) -> None:
        """Validates test environment.

        Populates test_case_data with the test number, name, description, etc.
        """
        super().setUp()
        self.test_case_data = TestCaseData.generate_from_id(self.id())

    def run_test(self, verbosity: Verbosity = Verbosity.DEFAULT) -> None:
        """Execute the test case after setting the verbosity level.

        Args:
            verbosity: Optional; Desired verbosity level for this test case (see: TEST v1.2.0).
        """
        self.set_verbosity(verbosity=verbosity)  # Test env variable against author's wishes
        super().run_test(verbosity=self._verbosity)  # Use that as the new verbosity level

    def tearDown(self) -> None:
        """Tear down the testing environment."""
        # Unlock files
        self._unlock_all_files()

        # Delete temporary files
        for cleanup_file in self._cleanup_file_list:
            delete_file(cleanup_file, ignore_missing=True)

        # Delete temporary directories
        self._cleanup_dir_list = list(set(self._cleanup_dir_list))  # Remove duplicates
        self._cleanup_dir_list.sort(key=len, reverse=True)  # Sort from longest to shortest
        for cleanup_dir in self._cleanup_dir_list:
            self._destroy_dir(cleanup_dir)

        super().tearDown()

    def validate_results(self) -> Any:
        """Verify results of execution."""
        raise NotImplementedError(
            self._test_error.format('The child class must override the validate_results method'))

    # COMMON-USE METHODS
    # Methods listed in alphabetical order
    def add_manual_arg(self, arg: str, value: Any) -> None:
        """Add a manual argument to the command list.

        Use this method to add -v to a command list or to use the --help argument.  Feel free
        to use this method in conjunction with any of the set_arg_*() methods.

        Args:
            arg: Non-empty string to add to the command list.
            value: A value to associate with arg in the command list.  Could be a string-based
                value, and empty string, or None.  Empty strings and None will be skipped in
                the command list.

        Raises:
            None: Calls self.fail() instead.
        """
        self._set_arg(arg=arg, value=value)

    def add_cleanup_file(self, filename: str) -> None:
        """Add a file to the cleanup list for removal.

        Validates a string is recieved, then adds it to the _cleanup_file_list.

        Args:
            filename: A name of a file to be be appended to the list.

        Raises:
            None: Calls self.fail() instead.
        """
        self._validate_string(validate_this=filename, param_name='filename', can_be_empty=False)
        self._cleanup_file_list.append(filename)

    def add_cleanup_dir(self, directory: str) -> None:
        """Add a directory to the cleanup list for removal.

        Validates a string is recieved, then adds it to the _cleanup_dir_list.

        Args:
            directory: A name of a directory to be be appended to the list.

        Raises:
            None: Calls self.fail() instead.
        """
        self._validate_string(validate_this=directory, param_name='directory', can_be_empty=False)
        self._cleanup_dir_list.append(directory)

    def construct_cmd_list(self, preamble: list) -> None:
        """Construct the test case command list.

        Command list is constructed based on caller-provided values (see: preamble) and test author
        input (e.g., _set_arg()).  The ArgManager object is queried for the user input.

        Args:
            preamble: A list prepended to the command list queried from ArgManager.  Commonly,
                ['python', 'eggsecutable.egg'].  This value can be empty.
        """
        # LOCAL VARIABLES
        cmd_list = preamble  # List of commands to execute for this test

        # VALIDATION
        # Input
        self._validate_list(validate_this=preamble, param_name='preamble', can_be_empty=True)

        # UPDATE COMMAND LIST
        try:
            cmd_list += self._arg_mngr_obj.get_cmd_list()
        except (TypeError, ValueError) as err:
            self.fail(self._test_error.format('ArgManager failed to construct the command list '
                                              f'with {str(err)}'))

        # DONE
        self.set_command_list(cmd_list)

    def create_dir(self, dirname: str, ignore_existing: bool = False,
                   cleanup: bool = True) -> None:
        """Create a directory.

        Call this method prior to run_test() to create a temporary directory at test-time.  Calls
        hobo.disk_operations.create_dir() under the hood.  Consider creating test case specific
        temporary directories for tests like "read-only directory" and set them to cleanup.
        Usage:
            self.create_dir(os.path.join(self.def_out_test_path, 'temp_dir'), cleanup=True)

        Args:
            dirname: Absolute or relative directory to create.
            ignore_existing: Optional; If True, don't error if it exists.
            cleanup: Optional; Delete this directory during test case TearDown().
                WARNING: Take care when using this option.  To destroy the directory, it must
                be emptied first!

        Raises:
            None: Instead, it calls self.fail().
        """
        # INPUT VALIDATION
        self._validate_type(cleanup, 'cleanup', bool)
        # All other input arguments are validated by create_file()

        # CREATE IT
        try:
            create_dir(dirname=dirname, ignore_existing=ignore_existing)
        except (FileExistsError, TypeError, ValueError) as err:
            self.fail(self._test_error.format(f'Creation of {dirname} failed with {str(err)}'))
        else:
            if cleanup:
                self._cleanup_dir_list.append(dirname)

    def create_file(self, filename: str, contents: str = '', ignore_existing: bool = False,
                    cleanup: bool = True) -> None:
        """Create a file.

        Call this method prior to run_test() to create a temporary file at test-time.  Calls
        hobo.disk_operations.create_file() under the hood.

        Args:
            filename: Absolute or relative filename to create.
            contents: Optional; Contents of filename.
            ignore_existing: Optional; If True, overwrite filename if it exists.
            cleanup: Optional; Delete this file during test case TearDown().

        Raises:
            None: Instead, it calls self.fail().
        """
        # INPUT VALIDATION
        self._validate_type(cleanup, 'cleanup', bool)
        # All other input arguments are validated by create_file()

        # CREATE IT
        try:
            create_file(filename=filename, contents=contents, ignore_existing=ignore_existing)
        except (FileExistsError, TypeError, ValueError) as err:
            self.fail(self._test_error.format(f'Creation of {filename} failed with {str(err)}'))
        else:
            if cleanup:
                self._cleanup_file_list.append(filename)

    def get_test_name(self) -> str:
        """Gets the full test name.

        Returns:
            Test name in the format Nebs_<NN> ex 'Normal_01'
        """
        return self.test_case_data.name

    def lock_file(self, file_to_lock: str) -> None:
        """Lock a file during test case execution.

        The file_to_lock must exist when this method is called.  File will be immediately opened,
        and held open.  Any locked files will be automatically released during tearDown().

        Args:
            file_to_lock: Absolute or relative filename to lock.
        """
        # INPUT VALIDATION
        self._validate_file(file_to_lock, 'file_to_lock', must_exist=True)

        # LOCK IT
        self._lock_file(file_to_lock=file_to_lock)

    def restore_permissions(self) -> None:
        """Restore permissions for all self._restore_perms entries.

        Any calls to self.set_*(recover=True) permission methods (e.g., ro, no_read) will be
        recovered when this method is called.
        """
        # Restore permissions
        for restore_file, restore_perms in self._restore_perms:
            self._set_perms(path=restore_file, mode=restore_perms)

    def set_dir_ro(self, dirname: str, ignore_missing: bool = False, recover: bool = True) -> None:
        """Make a directory read-only.

        Removes all write permissions from dirname.

        Args:
            dirname: A relative or absolute directory name to remove write permissions from.
            ignore_missing: Optional; If True, ignore any FileNotFoundError exceptions.
            recover: Optional; If True, restore the directory's permissions during tearDown()
        """
        # INPUT VALIDATION
        self._validate_type(recover, 'recover', bool)
        self._validate_type(ignore_missing, 'ignore_missing', bool)
        self._validate_directory(dirname, 'dirname', must_exist=not ignore_missing)

        # SET IT
        self._remove_write_perms(path=dirname, ignore_missing=ignore_missing, recover=recover)

    def set_dir_no_read(self, dirname: str, ignore_missing: bool = False,
                        recover: bool = True) -> None:
        """Remove read permissions from a directory.

        Removes all read permissions from dirname.

        Args:
            dirname: A relative or absolute directory name to remove read permissions from.
            ignore_missing: Optional; If True, ignore any FileNotFoundError exceptions.
            recover: Optional; If True, restore the file's permissions during tearDown()
        """
        # INPUT VALIDATION
        self._validate_type(recover, 'recover', bool)
        self._validate_type(ignore_missing, 'ignore_missing', bool)
        self._validate_directory(dirname, 'dirname', must_exist=not ignore_missing)

        # SET IT
        self._remove_read_perms(path=dirname, ignore_missing=ignore_missing, recover=recover)

    def set_file_no_read(self, filename: str, ignore_missing: bool = False,
                         recover: bool = True) -> None:
        """Make a file read-only.

        Removes all write permissions from filename.

        Args:
            filename: A relative or absolute filename to remove write permissions from.
            ignore_missing: Optional; If True, ignore any FileNotFoundError exceptions.
            recover: Optional; If True, restore the file's permissions during tearDown()
        """
        # INPUT VALIDATION
        self._validate_type(recover, 'recover', bool)
        self._validate_type(ignore_missing, 'ignore_missing', bool)
        self._validate_file(filename, 'filename', must_exist=not ignore_missing)

        # SET IT
        self._remove_read_perms(path=filename, ignore_missing=ignore_missing, recover=recover)

    def set_file_ro(self, filename: str, ignore_missing: bool = False,
                    recover: bool = True) -> None:
        """Make a file read-only.

        Removes all write permissions from filename.

        Args:
            filename: A relative or absolute filename to remove write permissions from.
            ignore_missing: Optional; If True, ignore any FileNotFoundError exceptions.
            recover: Optional; If True, restore the file's permissions during tearDown()
        """
        # INPUT VALIDATION
        self._validate_type(recover, 'recover', bool)
        self._validate_type(ignore_missing, 'ignore_missing', bool)
        self._validate_file(filename, 'filename', must_exist=not ignore_missing)

        # SET IT
        self._remove_write_perms(path=filename, ignore_missing=ignore_missing, recover=recover)

    def set_manual_args(self, manual_args: list) -> None:
        """Override execution with list of arguments.

        Only use this method as a last resort.  Consider using the set_arg_*() and/or
        add_manual_arg() methods instead.  *Definitely* don't use both.

        Args:
            manual_args: A list of non-empty strings to use as the command list.

        Raises:
            None: Instead, it calls self.fail().
        """
        try:
            self._arg_mngr_obj.set_cmd_list(manual_args)
        except (TypeError, ValueError, RuntimeError) as err:
            self.fail(self._test_error.format(f'Failed to set command list as {manual_args} '
                                              f'with {str(err)}'))

    def set_verbosity(self, verbosity: Verbosity = Verbosity.DEFAULT) -> None:
        """Detemine the desired verbosity for this test case.

        This method will allow the test author to indicate their desired level of verbosity.
        This may be overridden by TEST's Verbose Override feature.

        Args:
            verbosity: Optional; Desired verbosity level for this test case.

        Raises:
            None: Instead, it calls self.fail().
        """
        self._verbosity = verbosity  # Store it...
        self._validate_verbosity()   # ...then check it

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
    # pylint: disable=broad-exception-caught
    def _copy_file(self, src: str, dst: str) -> str:
        """Copies a file and its metadata from src to dest.

        Wraps a call to shutil.copy2() in a method to translate exceptions to self.fail() calls.

        Args:
            src: Source file, absolute or relative, to copy.  Must exist.
            dst: Destination to copy src to.  This can be a filename or directory.

        Returns:
            The copied file's filename.

        Raises:
            None: Instead, it calls self.fail().
        """
        # LOCAL VARIABLES
        file_dst = ''  # Return value from shutil.copy2()

        # INPUT VALIDATION
        self._validate_file(filename=src, param_name='src', must_exist=True)
        self._validate_string(validate_this=dst, param_name='dst', can_be_empty=False)

        # COPY IT
        try:
            file_dst = shutil.copy2(src=src, dst=dst)
        except PermissionError as err:
            self.fail_test_case(f'Permission error... {str(err)}')
        except (shutil.SameFileError, IOError, OSError) as err:
            self.fail_test_case(f'Error copying {src} to {dst}... {str(err)}')
        except Exception as err:
            self.fail_test_case(f'Unexpected error while copying {src} to {dst}... {str(err)}')

        # DONE
        return file_dst

    def _delete_file(self, filename: str, ignore_missing: bool = True) -> None:
        """Wraps hobo.disk_operations.delete_file() to translate exceptions to fail()s.

        Deletes file found in filename and will ignore exceptions if the file can't be found.

        Args:
            filename: The relative or absolute filename of the file to delete.
            ignore_missing: Optional; If False, calls self.fail() if the file can't be found.

        Raises:
            None: Calls self.fail() instead.
        """
        try:
            delete_file(filename=filename, ignore_missing=ignore_missing)
        except (OSError, TypeError, ValueError) as err:
            self.fail_test_case(f'Failed to delete {filename} with {str(err)}')

    def _delete_files(self, dirname: str, exempt: list = None) -> None:
        """Wraps hobo.disk_operations.delete_files() to translate exceptions to fail()s.

        Deletes all files found in dirname.

        Args:
            dirname: The relative or absolute pathname of the directory to destroy.

        Raises:
            None: Calls self.fail() instead.
        """
        try:
            delete_files(dirname=dirname, exempt=exempt)
        except (OSError, TypeError, ValueError) as err:
            self.fail_test_case(f'Failed to delete files in {dirname} with {str(err)}')

    def _destroy_dir(self, dirname: str) -> None:
        """Wraps hobo.disk_operations.destroy_dir() to translate exceptions to fail()s.

        Deletes all files and sub-directories in a directory, then removes the directory.

        Args:
            dirname: The relative or absolute pathname of the directory to empty.
            exempt: Optional; A list of filenames, as strings, to avoid deleting.

        Raises:
            None: Calls self.fail() instead.
        """
        try:
            destroy_dir(dirname=dirname)
        except (OSError, TypeError, ValueError) as err:
            self.fail(self._test_error.format(f'Failed to destroy directory {dirname} with '
                                              f'{str(err)}'))

    def _execute_subprocess_cmd(self, list_of_cmds: list, set_cwd: str = None) -> Tuple[str, str]:
        """Executes a set of commands using subprocess' Popen.

        Wraps hobo.subprocess_wrapper's execute_subprocess_cmd() in a class method to utilize
        self.fail().  Some input validation is handled by execute_subprocess_cmd().

        Args:
            list_of_cmds: A list of commands to execute in subprocess.
            set_cwd: Optional; Passed to subprocess.Popen() as the cwd keyword argument.

        Returns:
        A tuple containing stdout and stderr.

        Raises:
            None.  Calls self.fail() instead.
        """
        # LOCAL VARIABLES
        output_tuple = None  # Return value from execute_subprocess_cmd()

        # INPUT VAILIDATION
        self._validate_list(validate_this=list_of_cmds, param_name='list_of_cmds',
                            can_be_empty=False)
        for command in list_of_cmds:
            self._validate_string(validate_this=command, param_name='list_of_cmds entry',
                                  can_be_empty=False)
        if set_cwd:
            self._validate_string(validate_this=set_cwd, param_name='set_cwd', can_be_empty=False)

        # VALIDATION
        try:
            output_tuple = execute_subprocess_cmd(list_of_cmds=list_of_cmds, set_cwd=set_cwd)
        except (TypeError, ValueError, RuntimeError) as err:
            self.fail_test_case(f'Command list {" ".join(list_of_cmds)} failed with {str(err)}')

        # DONE
        return output_tuple

    def _generate_md5_hash(self, filename: str) -> str:
        """Generate an md5 message digest for filename.

        Method calls hobo.disk_operations calc_file_md5sum() under the hood.

        Args:
            filename: Relative or absolute filename to generate an md5 message digest for.

        Returns:
            A string containing the md5 message digest.

        Raises:
            None: Calls self.fail() or self._add_test_failure() as appropriate.
        """
        # LOCAL VARIABLES
        md5sum = ''  # MD5 hash of filename

        # DO IT
        try:
            md5sum = calc_file_md5sum(Path(filename))
        except (FileNotFoundError, OSError, TypeError, ValueError) as err:
            self._add_test_failure(f'Failed to calculate md5 hash of {filename} '
                                   f'with {str(err)}')

        # DONE
        return md5sum

    def _get_perms(self, path: str, ignore_missing: bool) -> int:
        """Get permissions, as an int, for path.

        Does not validate input.  Convert the return value to an octal for something more readable.

        Args:
            path: Absolute or relative directory or file to get permissions for.
            ignore_missing: Ignore any 'file missing' errors.

        Returns:
            Operating-system mode bitfield. (see: os.stat().st_mode or oschmod.get_mode())
            Returns zero (0) if file is missing and ignore_missing is True.

        Raises:
            None: Instead, it calls self.fail().
        """
        # LOCAL VARIABLES
        template_err = 'Failed to get permissions for {} with {}'  # Template error
        mode = 0                                                   # OS mode bitfield

        # GET IT
        try:
            mode = oschmod.get_mode(path)
        except FileNotFoundError as fnf_err:
            if not ignore_missing:
                self.fail(self._test_error.format(template_err.format(path, str(fnf_err))))
        except (TypeError, ValueError, OSError) as err:
            self.fail(self._test_error.format(template_err.format(path, str(err))))

        # DONE
        return mode

    def _get_subprocess_cmd_exit(self, list_of_cmds: list, set_cwd: str = None) -> int:
        """Executes a set of commands using subprocess' Popen.

        Wraps hobo.subprocess_wrapper's get_subprocess_cmd_exit() in a class method to utilize
        self.fail().  Input validation is handled by get_subprocess_cmd_exit().

        Args:
            list_of_cmds: A list of commands to execute in subprocess.
            set_cwd: Optional; Passed to subprocess.Popen() as the cwd keyword argument.

        Returns:
            An integer representing the exit code.

        Raises:
            None.  Calls self.fail() instead.
        """
        # LOCAL VARIABLES
        error_message = ''  # Store the error message here
        exit_code = 0       # Process exit code

        # VALIDATION
        try:
            exit_code = get_subprocess_cmd_exit(list_of_cmds=list_of_cmds, set_cwd=set_cwd)
        except (TypeError, ValueError, RuntimeError) as err:
            error_message = self._test_error.format(str(err))

        # REPORTING
        if error_message:
            self.fail(error_message)

        # DONE
        return exit_code

    # pylint: disable=broad-exception-caught
    def _list_files(self, dirname: str, include_dirname: bool = False) -> list:
        """List file names found in a directory.

        Wraps hobo.disk_operations's list_files() in a class method to utilize self.fail().  Input
        validation is handled by list_files().

        Args:
            dirname: The relative or absolute pathname of the directory to search.
            include_dirname: Optional; If True, includes the directory name with each file name
                in the returned list.

        Returns:
            A list of file names found in dirname. If there are no files found in dirname, the list
            will be empty.

        Raises:
            None.  Calls self.fail() instead.
        """
        # LOCAL VARIABLES
        file_list = []  # List of files found in dirname

        # DO IT
        try:
            file_list = list_files(dirname=dirname, include_dirname=include_dirname)
        except (TypeError, ValueError) as err:
            self.fail(self._test_error.format('Bad Input... ' + str(err)))
        except (FileNotFoundError, OSError) as err:
            self.fail(self._test_error.format('Bad Environment... ' + str(err)))
        except Exception as err:
            self.fail(self._test_error.format('Unanticipated error... ' + str(err)))

        # DONE
        return file_list

    def _lock_file(self, file_to_lock: str) -> None:
        """Open a file in append-mode and store the stream object.

        Does not validate input.

        Args:
            file_to_lock: Absolute or relative filename to lock.
        """
        # LOCAL VARIABLES
        open_file_obj = None  # <class '_io.TextIOWrapper'> returned by open()

        # LOCK IT
        try:
            # pylint: disable=consider-using-with
            open_file_obj = open(file_to_lock, 'a', encoding='utf-8')
            # pylint: enable=consider-using-with
        except OSError as err:
            self.fail_test_case(f'Failed to "open({file_to_lock}, "a")" with {err}')
        except Exception as err:
            self.fail_test_case(f'Unanticipated exception from "open({file_to_lock}, "a")": {err}')
        else:
            self._locked_file_objs.append(open_file_obj)

    def _set_arg(self, arg: str, value: str) -> None:
        """Wraps the call to ArgManager.add_arg().

        Wraps interaction with the ArgManager object.  Sets argument/value pairs on behalf of the
        test author.

        Args:
            arg: Command line argument to add to the object.
            value: The value to associate with arg.  This can be None or an empty string for on/off
                argument flags.

        Raises:
            None: Calls self.fail() instead.
        """
        try:
            self._arg_mngr_obj.add_arg(arg=arg, value=value, overwrite=False)
        except (TypeError, ValueError, KeyError) as err:
            self.fail(self._test_error.format(f'Failed to set {arg}:{value} with {str(err)}'))

    def _remove_read_perms(self, path: str, ignore_missing: bool, recover: bool) -> None:
        """Make a path, file or directory, unreadable.

        Does not validate input.  Removes all read permissions from path.

        Args:
            path: Absolute or relative directory or file to remove read permissions for.
            ignore_missing: Ignore any 'file missing' errors.
            recover: Restore the original permissions during the test case TearDown().

        Raises:
            None: Instead, it calls self.fail().
        """
        # LOCAL VARIABLES
        cur_perms = 0  # Current permissions
        new_perms = 0  # Read-only permissions derived from cur_perms

        # SET IT
        # Get current permissions
        cur_perms = self._get_perms(path, ignore_missing)
        # Exists?
        if cur_perms:
            # Recover?
            if recover:
                self._restore_perms.append(tuple((path, cur_perms)))
            # Create new mask
            new_perms = cur_perms & ~(stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH)
            # Set new permissions
            self._set_perms(path, new_perms)

    def _remove_write_perms(self, path: str, ignore_missing: bool, recover: bool) -> None:
        """Make a path, file or directory, read-only.

        Does not validate input.  Removes all write permissions from path.

        Args:
            path: Absolute or relative directory or file to remove write permissions for.
            ignore_missing: Ignore any 'file missing' errors.
            recover: Restore the original permissions during the test case TearDown().

        Raises:
            None: Instead, it calls self.fail().
        """
        # LOCAL VARIABLES
        cur_perms = 0  # Current permissions
        new_perms = 0  # Read-only permissions derived from cur_perms

        # SET IT
        # Get current permissions
        cur_perms = self._get_perms(path, ignore_missing)
        # Exists?
        if cur_perms:
            # Recover?
            if recover:
                self._restore_perms.append(tuple((path, cur_perms)))
            # Create new mask
            new_perms = cur_perms & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            # Set new permissions
            self._set_perms(path, new_perms)

    def _set_perms(self, path: str, mode: int) -> None:
        """Set permissions, as an int, for path.

        Does not validate input.  Convert the return value to an octal for something more readable.

        Args:
            path: Absolute or relative directory or file to set permissions for.
            mode: Operating-system mode bitfield. (see: os.chmod() or oschmod.set_mode())

        Raises:
            None: Instead, it calls self.fail().
        """
        try:
            oschmod.set_mode(path, mode)
        except (TypeError, ValueError, FileNotFoundError, OSError) as err:
            self.fail(self._test_error.format(f'Failed to set mode {mode} for path {path} with '
                                              f'{str(err)}'))

    def _unlock_all_files(self) -> None:
        """Unlock all files found in self._locked_file_objs."""
        for locked_file in self._locked_file_objs:
            if locked_file and hasattr(locked_file, 'close'):
                locked_file.close()
# pylint: enable=invalid-name,attribute-defined-outside-init
