"""Defines bespoke AIS exceptions for use in this sub-package."""


class AISIntegrityFailure(Exception):
    """An AIS payload has failed its integrity check."""


class AISPayloadInvalid(Exception):
    """An AIS payload value has failed a validity check."""
