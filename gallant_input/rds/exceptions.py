"""Defines bespoke RDS exceptions for use in this sub-package."""


class RDSIntegrityFailure(Exception):
    """An RDS block has failed its integrity check."""
    pass


class RDSBlockIDMismatch(Exception):
    """An RDS block does not match the expected Block ID."""
    pass
