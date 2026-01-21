"""Unit test module for AISPayloadInfo.mid.

Typical Usage:
    python -m test                                           # Run *all* the test cases
    python -m test.unit_test                                 # Run *all* the unit test cases
    python -m test.unit_test.test_ais                        # Run *all* ais sub-package test cases
    python -m test.unit_test.test_ais.test_ais_payload_info         # Run *all* AISPayloadInfo method test cases
    # Run just these unit tests
    python -m test.unit_test.test_ais.test_ais_payload_info.test_ais_payload_info_mid
    # Run just this normal 1 unit test
    python -m test.unit_test.test_ais.test_ais_payload_info.test_ais_payload_info_mid -k n01
"""

# Standard Imports
from typing import Any
from unittest import skip
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
# Local Imports
from gallant_input.ais.payload_info import AISPayloadInfo
# from test.unit_test.test_ais.test_ais_payload_info.test_ais_payload_info import AISPayloadInfoUnitTest
from test.unit_test.test_ais.test_ais_payload_info import AISPayloadInfoUnitTest


class AISPayloadInfoMidUnitTest(AISPayloadInfoUnitTest):
    """Parent class for all AISPayloadInfo.mid unit tests."""

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        test_obj = self.create_aispayloadinfo(*self._args, **self._kwargs)
        return test_obj.mid

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order

    def run_test_exception(self, test_input: Any, exception_type: Exception,
                           exception_msg: str) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            test_input: The AISPayloadInfo() argument.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
        """
        self.set_test_input(test_input)
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, test_input: bytes, exp_return: int) -> None:
        """Common method calls for a test case expected to return.

        Args:
            test_input: Well-formed AIS payload as a binary bytes string to use as the
                AISPayloadInfo() argument.
            exp_return: The expected value of AISPayloadInfo.mid.
        """
        self.set_test_input(test_input)
        self.expect_return(exp_return)
        self.run_test()


class NormalAISPayloadInfoMidUnitTest(AISPayloadInfoMidUnitTest):
    """Normal Test Cases."""

    def test_n01_ais_repo_default(self):
        """Valid example of RDS Block A."""
        test_input = self.GOOD_AIS_PAYLOAD1
        exp_return = 247
        self.run_test_return(test_input, exp_return)


class ErrorAISPayloadInfoMidUnitTest(AISPayloadInfoMidUnitTest):
    """Error Test Cases."""

    def test_e01_placeholder(self):
        """Placeholder."""
        pass


class SpecialAISPayloadInfoMidUnitTest(AISPayloadInfoMidUnitTest):
    """Special Test Cases."""

    def test_s01_placeholder(self):
        """Placeholder."""
        pass


if __name__ == '__main__':
    execute_test_cases()
