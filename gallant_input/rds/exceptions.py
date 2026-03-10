"""Defines bespoke RDS exceptions for use in this sub-package."""


class RDSBlockIDMismatch(Exception):
    """An RDS block does not match the expected Block ID."""


class RDSDataIncomplete(Exception):
    """RDS data does not include all offsets/segments to form the complete data."""


class RDSFeatureUnavailable(Exception):
    """An RDS group + version does not implement a particular feature."""


class RDSIntegrityFailure(Exception):
    """An RDS block has failed its integrity check."""


class RDSMsgGroupTypeMissing(Exception):
    """Unable to locate a particular Message Group Type."""


class RDSPICodeMismatch(Exception):
    """An RDS group's Program Identification code (PI code) does not match the expected code."""
