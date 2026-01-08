"""Defines bespoke RDS exceptions for use in this sub-package."""


class RDSFeatureUnavailable(Exception):
    """An RDS group + version does not implement a particular feature."""


class RDSBlockIDMismatch(Exception):
    """An RDS block does not match the expected Block ID."""


class RDSIntegrityFailure(Exception):
    """An RDS block has failed its integrity check."""


class RDSPICodeMismatch(Exception):
    """An RDS group's Program Identification code (PI code) does not match the expected code."""
