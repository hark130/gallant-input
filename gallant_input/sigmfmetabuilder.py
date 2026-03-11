"""Functionality to easily build up SigMF metadata."""

# Standard Imports
from typing import Any, List
# Third Party Imports
import sigmf
# Local Imports
from gallant_input.constants import (SIG_ANNO_START_INDEX_KEY, SIG_CAP_DATETIME_KEY,
                                     SIG_CAP_FREQUENCY_KEY, SIG_CAP_START_INDEX_KEY,
                                     SIG_GLOB_AUTHOR_KEY, SIG_FIELD_ANNOTATION_KEY,
                                     SIG_FIELD_CAPTURE_KEY, SIG_FIELD_GLOBAL_KEY,
                                     SIG_GLOB_DATATYPE_KEY, DEF_USERNAME,
                                     SIG_GLOB_DESCRIPTION_KEY, SIG_GLOB_SAMPLE_RATE_KEY,
                                     SIG_GLOB_VERSION_KEY)
from gallant_input.sigmfdatatype import SigMFDataType
from gallant_input.validation import (validate_bool, validate_int, validate_int_or_float,
                                      validate_string, validate_type)


def build_annotations_array(sample_start: int = 0) -> List[dict[str:Any]]:
    """Build a SigMF annotations array for use as a 'annotations' value in the metadata dictionary.

    See: https://sigmf.org/#subsec:AnnotationsArray

    Args:
        sample_start: [OPTIONAL] The sample index at which this Segment takes effect.

    Returns:
        An annotations array list of dictionaries with sigmf.SigMFFile.*_KEY as keys with the
        arguments as values.

    Raises:
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES
    annotations_dict = {}                 # SigMF Captures object dict of SigMFFile.*_KEY keys/vals
    min_samp_start = 0                    # Minimum value for sample_start
    max_samp_start = 9223372036854775807  # Maximum value for sample_start

    # BUILD IT
    # sample_start
    validate_int(sample_start, 'sample_start')
    if sample_start < 0 or sample_start > max_samp_start:
        raise ValueError(f'The "sample_start" value of "{sample_start}" violates the SigMF '
                         f'standard of minimum : {min_samp_start} maximum : {max_samp_start}')
    annotations_dict[SIG_ANNO_START_INDEX_KEY] = sample_start

    # DONE
    return [annotations_dict]


def build_captures_array(sample_start: int = 0, date_time: str | None = None,
                         center_freq: float | None = None) -> List[dict[str:Any]]:
    """Build a SigMF captures array list for use as a 'captures' value in the metadata dictionary.

    See: https://sigmf.org/#subsec:CapturesArray

    Args:
        sample_start: [OPTIONAL] Index of first sample of this chunk.
            This value may not be None because it is required.
        date_time: [OPTIONAL] An ISO-8601 string indicating the timestamp of the sample index
            specified by sample_start.  Use spacetime.create_rfc_3339_z_time() to generate a valid
            string.
        center_freq: [OPTIONAL] The center frequency of the signal in Hz.

    Returns:
        A captures array list of dictionaries with sigmf.SigMFFile.*_KEY as keys with the
        arguments as values.

    Raises:
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES
    captures_dict = {}                   # SigMF Captures object dict of SigMFFile.*_KEY keys/vals
    max_sam_start = 9223372036854775807  # Maximuium value for sample start
    min_cen_freq = -1000000000000        # Minimum value for center_freq
    max_cen_freq = 1000000000000         # Maximum value for center_freq

    # BUILD IT
    # sample_start
    validate_int(sample_start, 'sample_start')
    if sample_start < 0 or sample_start > max_sam_start:
        raise ValueError(f'The "sample_start" value of "{sample_start}" violates the SigMF '
                         f'standard of minimum : 0 maximum : {max_sam_start}')
    captures_dict[SIG_CAP_START_INDEX_KEY] = sample_start
    # date_time
    if date_time is not None:
        validate_string(date_time, 'date_time', can_be_empty=False)
        captures_dict[SIG_CAP_DATETIME_KEY] = date_time
    # center_freq
    if center_freq is not None:
        validate_float(center_freq, 'center_freq')
        if center_freq < min_cen_freq or center_freq > max_cen_freq:
            raise ValueError(f'The "center_freq" value of "{center_freq}" violates the SigMF '
                             f'standard of minimum : {min_cen_freq} maximum : {max_cen_freq}')
        captures_dict[SIG_CAP_FREQUENCY_KEY] = center_freq

    # DONE
    return [captures_dict]


def build_dataset_format(is_complex: bool = True, data_type: SigMFDataType = SigMFDataType.FLOAT,
                         bit_width: int = 32, little_e: bool = True) -> str:
    """Build a SigMF Dataset Format that conforms with Augmented Backus-Naur form (ABNF) rules.

    Only IEEE-754 single-precision and double-precision floating-point types are supported by
    the SigMF Core namespace. Note that complex data types are specified by the bit width of
    the individual I/Q components, and not by the total complex pair bitwidth (like Numpy).

    Args:
        is_complex: [OPTIONAL] If True, 'c'.  Otherise it's real: 'r'.
        data_type: [OPTIONAL] SigMFDataType int enum indicating the dataset format data type.
        bit_width: [OPTIONAL] The number of bits in each sample.  Supported values: 8, 16, 32, 64.
        little_e: [OPTIONAL] If True, '_le' for little-endian.  Otherwise it's '_be' for big-endian.
            This argument is ignored if num_bits is 8.

    Returns:
        An ABNF-compliant dataset value.  Default return value is 'cf32_le'.

    Raises:
        LookupError: UNDEFINED SigMFDataType.
        NotImplementedError: Any IntEnum values added to SigMFDataType that weren't also
            implemented in the SigMFDataType.translate property method.
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES
    valid_widths = [8, 16, 32, 64]  # Supported bit widths
    data_format = ''                # ABNF-compliant SigMF Dataset Format

    # INPUT VALIDATION
    validate_bool(is_complex, 'is_complex')
    validate_type(data_type, 'data_type', SigMFDataType)
    validate_int(bit_width, 'bit_width')
    if bit_width not in valid_widths:
        raise ValueError(f'The "bit_width" value "{bit_width}" is not in {valid_widths}')
    validate_bool(little_e, 'little_e')

    # BUILD IT
    # Complex or Real
    if is_complex:
        data_format = data_format + 'c'
    else:
        data_format = data_format + 'r'
    # Data Type
    data_format = data_format + data_type.translate
    # Bit Width
    data_format = data_format + str(bit_width)
    # Endianness
    if bit_width > 8:
        if little_e:
            data_format = data_format + '_le'
        else:
            data_format = data_format + '_be'

    # DONE
    return data_format


def build_default_metadata(dataset_format: str = 'cf32_le', samp_rate: int | float | None = None,
                           date_time: str | None = None,
                           center_freq: float | None = None) -> dict[str:Any]:
    """Build a basic SigMF metadata dictionary.

    Creates a basic dictionary with a global object, captures array, and an annotations array.

    Args:
        dataset_format: [OPTIONAL] A non-empty string w/ a SigMF Dataset Format that conforms with
            Augmented Backus-Naur form (ABNF) rules.  Use build_dataset_format() to build this str.
            This value may not be None because it is required.
        samp_rate: [OPTIONAL] The sampling frequency in Hz.
        date_time: [OPTIONAL] An ISO-8601 string indicating the timestamp of the sample index
            specified by sample_start.  Use spacetime.create_rfc_3339_z_time() to generate a valid
            string.
        center_freq: [OPTIONAL] The center frequency of the signal in Hz.

    Returns:
        A basic SigMF dictionary containing a global object, captures array, and an
        annotations array.

    Raises:
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES
    metadata_dict = {}  # The SigMF metadata dictionary

    # BUILD IT
    metadata_dict[SIG_FIELD_GLOBAL_KEY] = build_global_object(dataset_format=dataset_format,
                                                              samp_rate=samp_rate)
    metadata_dict[SIG_FIELD_CAPTURE_KEY] = build_captures_array(date_time=date_time,
                                                                center_freq=center_freq)
    metadata_dict[SIG_FIELD_ANNOTATION_KEY] = build_annotations_array()

    # DONE
    return metadata_dict


def build_global_object(dataset_format: str = 'cf32_le', samp_rate: int | float | None = None,
                        author: str | None = DEF_USERNAME, description: str | None = None,
                        version: str = sigmf.__version__) -> dict[str:Any]:
    """Build a SigMF global object dictionary for use as a 'global' value in the metadata dict.

    See: https://sigmf.org/#subsec:GlobalObject

    Args:
        dataset_format: [OPTIONAL] A non-empty string w/ a SigMF Dataset Format that conforms with
            Augmented Backus-Naur form (ABNF) rules.  Use build_dataset_format() to build this str.
            This value may not be None because it is required.
        samp_rate: [OPTIONAL] The sampling frequency in Hz.
        author: [OPTIONAL] A text identifier for the author potentially including name, handle,
            email, and/or other ID like Amateur Call Sig.
        description: [OPTIONAL] A text description of the SigMF Recording.
        version: [OPTIONAL] The version of the SigMF specification used to create the
            Metadata file, in the X.Y.Z format.  This value may not be None because it is required.

    Returns:
        A global object dictionary of sigmf.SigMFFile.*_KEY as keys with the arguments as values.

    Raises:
        TypeError: Bad data type.
        ValueError: Invalid value.
    """
    # LOCAL VARIABLES
    global_dict = {}               # SigMF Global object dict of SigMFFile.*_KEY key/value pairs
    max_samp_rate = 1000000000000  # Maximum value for samp_rate

    # BUILD IT
    # dataset_format
    validate_string(validate_this=dataset_format, param_name='dataset_format', can_be_empty=False)
    global_dict[SIG_GLOB_DATATYPE_KEY] = dataset_format
    # samp_rate
    if samp_rate is not None:
        validate_int_or_float(samp_rate, 'samp_rate')
        if samp_rate < 0 or samp_rate > max_samp_rate:
            raise ValueError(f'The "samp_rate" value of "{samp_rate}" violates the SigMF standard '
                             f'of minimum : 0 maximum : {max_samp_rate}')
        global_dict[SIG_GLOB_SAMPLE_RATE_KEY] = samp_rate
    # author
    if author is not None:
        validate_string(validate_this=author, param_name='author', can_be_empty=False)
        global_dict[SIG_GLOB_AUTHOR_KEY] = author
    # description
    if description is not None:
        validate_string(validate_this=description, param_name='description', can_be_empty=False)
        global_dict[SIG_GLOB_DESCRIPTION_KEY] = description
    # version
    validate_string(validate_this=version, param_name='version', can_be_empty=False)
    global_dict[SIG_GLOB_VERSION_KEY] = version

    # DONE
    return global_dict
