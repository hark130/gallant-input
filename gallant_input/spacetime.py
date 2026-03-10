"""Functionality to manage date, time, and geospatial coordinates.

According to Einstein's theories of relativity, space and time are fundamentally intertwined as
a four-dimensional continuum known as spacetime... so, here we are.
"""

# Standard Imports
from datetime import datetime, timezone
# Third Party Imports
# Local Imports
from gallant_input.validation import validate_bool, validate_type


def create_rfc_3339_z_time(date_time: datetime | None = None, frac_sec: bool = True) -> str:
    """Create an RFC-3339, ISO-8601 compliant datetime string.

    Utilizes Coordinated Universal Time (UTC) and provides the result where the time-offset is Z.
    This function was intended for use when generating SigMF metadata (see: the sigmfmetabuilder
    module).

    Args:
        date_time: [OPTIONAL] The object to generate the string from.  If provided, will be
            converted to UTC.  If None then the current time, using  as the timezone, is used.
            See: datetime.now(timezone.utc).
        frac_sec: [OPTIONAL] If True, fractional seconds are preserved.

    Returns:
        An RFC-3339, ISO-8601 compliant datetime string.
    """
    # LOCAL VARIABLES
    datetime_str = None   # The formatted datetime string
    timespec = 'seconds'  # Specifies additional terms to include

    # INPUT VALIDATION
    # datetime
    if date_time is not None:
        validate_type(date_time, 'date_time', datetime)
        date_time = date_time.astimezone(timezone.utc)  # Convert to UTC
    else:
        date_time = datetime.now(timezone.utc)
    # frac_sec
    validate_bool(frac_sec, 'frac_sec')

    # CREATE IT
    if frac_sec:
        timespec = 'microseconds'
    datetime_str = date_time.isoformat(timespec=timespec).replace('+00:00', 'Z')

    # DONE
    return datetime_str
