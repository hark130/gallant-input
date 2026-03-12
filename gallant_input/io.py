"""Read, write, and manipulate file-based digital signal samples."""

# Standard Imports
from pathlib import Path
# Third Party Imports
from numpy.typing import DTypeLike
from sigmf import SigMFFile
import numpy
# Local Imports
from gallant_input.constants import SIGMF_DATA_FILE_EXT, SIGMF_META_FILE_EXT
from gallant_input.validation import (validate_bool, validate_path, validate_ndarray,
                                      validate_string, validate_type)


def write_samples(filename: str | Path, samples: numpy.ndarray,
                  sample_dtype: DTypeLike = numpy.complex64,
                  metadata: dict | None = None, overwrite: bool = False) -> None:
    """Write an array of complex samples to an IQ file or SigMF dataset.

    If metadata is provided, the format and file extensions will be updated to use the SigMF format.
    Otherwise, a raw binary IQ file is written.

    Args:
        filename: The relative or absolute output file path to save the samples to.  If metadata is
            provided, the file extension of this filename will be changed to match the SigMF
            format.
        samples: A 1-dimensional array of complex samples to write as interleaved I/Q pairs in
            binary format.  If the data type of the samples does not match sample_dtype then the
            data type of the samples will be updated to match.
        sample_dtype: The data type to save the samples as.  If this does not match the actual
            data type of samples then samples will be updated to match.  This argument supports
            numpy data types (e.g., numpy.complex128) and numpy.dtype objects
            (e.g., numpy.dtype('complex128')).
        metadata: [OPTIONAL] If defined, the format of the saved file will be changed to SigMF
            and this dictionary will be used as the sigmf-meta values.  This dictionary must
            pass SigMFFile().validate().  If used, the caller is responsible for ensuring all
            dictionary values reflect sample_dtype because the metadata dictionary will *not*
            be updated.
        overwrite: [OPTIONAL] If True and filename exists then filename will be overwritten.

    Raises:
        FileExistsError: The overwrite value is False but filename exists.
        OSError: The filename exists, overwrite is True, but filename is not a file.
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    file_path = filename   # The filename argument positively changed to be a Path object
    new_samp_dtype = None  # sample_dtype explicitly converted to a numpy.dtype object

    # INPUT VALIDATION
    # filename
    if isinstance(filename, str):
        file_path = Path(filename)
    _validate_write_samples(filename=file_path, samples=samples, sample_dtype=sample_dtype,
                            metadata=metadata, overwrite=overwrite)

    # PREPARE IT
    new_samp_dtype = numpy.dtype(sample_dtype)
    if samples.dtype != new_samp_dtype:
        samples = numpy.asarray(samples, dtype=new_samp_dtype)

    # WRITE IT
    if metadata is None:
        _validate_dest_filename(file_path, overwrite)
        samples.tofile(file_path)
    else:
        _write_sigmf_samples(filename=file_path, samples=samples, metadata=metadata,
                             overwrite=overwrite)


def _validate_dest_filename(filename: Path, overwrite: bool) -> None:
    """Validate the filename context vs overwriting on behalf of the module.

    This function does not validate its input (other than testing filename's existence).
    """
    # CONTEXT VALIDATION
    if filename.exists():
        if not overwrite:
            raise FileExistsError(f'The filename value "{filename.absolute()}" exists but '
                                  f'overwrite is set to {overwrite}')
        if not filename.is_file():
            raise OSError(f'The filename value "{filename.absolute()}" is not a file')


def _validate_dtype_like(dtlike: DTypeLike, param_name: str, must_be_complex: bool = True) -> None:
    """Validate a DTypeLike object on behalf of this module.

    Args:
        dtlike: The object to validate as a DTypeLike type.
        param_name: The name of the parameter to be used in exception messages.
        must_be_complex: [OPTIONAL] If true, verifies dtlike comforms to numpy.complex64
            or numpy.complex64 (after conversion to numpy.dtype()).

    Raises:
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # LOCAL VARIABLES
    test_dtlike = None  # The dtlike argument constructed as a numpy.dtype() object
    # Supported complex types (if must_be_complex is True)
    supp_complex = tuple((numpy.dtype('complex64'), numpy.dtype('complex128')))

    # INPUT VALIDATION
    validate_string(param_name, 'param_name', can_be_empty=True)
    validate_bool(must_be_complex, 'must_be_complex')
    try:
        test_dtlike = numpy.dtype(dtlike)
    except TypeError as err:
        raise TypeError(f'The "{param_name}" argument should have been a DTypeLike object '
                        f'but was "{type(dtlike)}" instead and rejected with {err}') from err
    except ValueError as err:
        raise ValueError(f'The "{param_name}" argument value of "{dtlike}" was rejected as a '
                         f'numpy.dtype() with "{err}" which indicates it is not compatible as '
                         'a DTypeLike object') from err
    if must_be_complex and test_dtlike not in supp_complex:
        raise ValueError(f'The converted "{param_name}" argument must be complex and, as such, '
                         f'must conform to one of the following "{supp_complex}" instead '
                         f'of "{type(test_dtlike)}"')


def _validate_write_samples(filename: Path, samples: numpy.ndarray,
                            sample_dtype: DTypeLike, metadata: dict | None,
                            overwrite: bool) -> None:
    """Validate the write_samples() arguments.

    Raises:
        FileExistsError: The overwrite value is False but filename exists.
        OSError: The filename exists, overwrite is True, but filename is not a file.
        TypeError: Bad data type.
        ValueError: Bad value.
    """
    # INPUT VALIDATION
    # filename
    validate_path(filename, 'filename (converted)', must_exist=False)
    # samples
    validate_ndarray(samples, 'samples', can_be_empty=False, num_dim=1)
    if not numpy.iscomplexobj(samples):
        raise ValueError('The "samples" argument must contain complex values intead of '
                         f'"{repr(samples.dtype)}"')
    # sample_dtype
    _validate_dtype_like(sample_dtype, 'sample_dtype', must_be_complex=True)
    # metadata
    if metadata is not None:
        validate_type(metadata, 'metadata', dict)
    # overwrite
    validate_bool(overwrite, 'overwrite')


def _write_sigmf_samples(filename: Path, samples: numpy.ndarray, metadata: dict,
                         overwrite: bool) -> None:
    """Write an array of samples to a SigMF dataset.

    This function does not validate its input (other than to compare the destination filenames
    vs overwrite).  The caller is expected to have:
    - Called _validate_write_samples()
    - Converted any filename strings to a Path object
    - Normalized the data type of the samples array

    However, sigmf.SigMFFile().validate is used to validate the metadata.
    """
    # LOCAL VARIABLES
    sigmf_obj = SigMFFile(metadata=metadata)  # The SigMFFile() object
    data_path = filename.with_suffix('.' + SIGMF_DATA_FILE_EXT)
    meta_path = filename.with_suffix('.' + SIGMF_META_FILE_EXT)

    # INPUT VALIDATION
    _validate_dest_filename(data_path, overwrite)
    _validate_dest_filename(meta_path, overwrite)
    try:
        sigmf_obj.validate()
    except (KeyError, TypeError, ValueError) as err:
        raise RuntimeError(f'The SigMF library rejected the metadata with {err}') from err

    # WRITE IT
    samples.tofile(data_path)
    sigmf_obj.tofile(meta_path, overwrite=overwrite)
