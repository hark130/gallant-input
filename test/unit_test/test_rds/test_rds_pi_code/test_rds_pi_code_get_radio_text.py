"""Unit test module for RDSPICode.get_radio_text().

Typical Usage:
    python -m test                                      # Run *all* the test cases
    python -m test.unit_test                            # Run *all* the unit test cases
    python -m test.unit_test.test_rds                   # Run *all* rds sub-package test cases
    python -m test.unit_test.test_rds.test_rds_pi_code  # Run *all* RDSPICode method test cases
    # Run just these unit tests
    python -m test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_get_radio_text
    # Run just this normal 1 unit test
    python -m test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_get_radio_text -k n01
"""

# Standard Imports
# Third Party Imports
from tediousstart.tediousstart import execute_test_cases
# Local Imports
from gallant_input.rds.constants import RDS_BLOCK_DATA_LEN, RDS_GROUP_LEN
from gallant_input.rds.exceptions import (RDSIntegrityFailure, RDSMsgGroupTypeMissing,
                                          RDSPICodeMismatch)
from test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code import RDSPICodeUnitTest


class RDSPICodeGRTUnitTest(RDSPICodeUnitTest):
    """Parent class for all RDSPICode.get_radio_text() unit tests.

    Attributes:
        test_case_data:   # Stores data about the test case as a TestCaseData object
        test_input_dir:   # Default input directory (OPTIONAL)
        test_output_dir:  # Default output directory (OPTIONAL)
        input_pi_code:    # Test case input: RDSPICode(pi_code)
        test_obj:         # RDSPICode() test object created by self.create_test_obj()
    """

    # CORE CLASS METHODS
    # Methods listed in call order

    def call_callable(self):
        """Defines how the class will invoke the method call."""
        return self.test_obj.get_radio_text(*self._args, **self._kwargs)

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call."""
        self._validate_return_value(return_value=return_value)

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def populate_test_object(self, pi_code: bytes, stream_bytes: bytes) -> None:
        """Creates the test object and adds all stream_bytes to it in RDSGroup length chunks.

        Args:
            pi_code: Sets the pi_code ctor argument input.  Must be valid input.  The RDSPICode
                ctor is effectively unit tested within the RDSPICode.verify_pi_code_integrity()
                unit tests.
                (See: test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_validate_integrity)
            stream_bytes: Any number of bytes to add to the RDSPICode object utilizing the
                add_bytes() method.  This argument's length *must* be valid (e.g., length must
                be a multiple of RDS_GROUP_LEN, must be valid RDSGroup, must be associated with
                pi_code).  RDSPICode.add_bytes() has its own dedicated unit tests.
        """
        # LOCAL VARIABLES
        stream_len = 0                # Length of stream_bytes
        start = 0                     # Starting index of stream_bytes to chunk
        stop = start + RDS_GROUP_LEN  # Ending index of stream_bytes to chunk

        # VALIDATION
        # pi_code
        self._validate_type(validate_this=pi_code, param_name='pi_code', param_type=bytes)
        # stream_bytes
        self._validate_type(validate_this=stream_bytes, param_name='stream_bytes', param_type=bytes)
        stream_len = len(stream_bytes)
        if stream_len == 0:
            self.fail_test_case('The stream_bytes argument may not be empty and must be valid')
        elif stream_len % RDS_GROUP_LEN:
            self.fail_test_case('The stream_bytes argument must be a multiple of '
                                f'{RDS_GROUP_LEN} in length instead of {stream_len}')

        # CREATE AND POPULATE
        try:
            self.create_test_obj(pi_code=pi_code)  # Creates self.test_obj, once
            while True:
                if stop > stream_len:
                    break  # All done
                self.test_obj.add_bytes(group_bytes=stream_bytes[start:stop])
                # Advance to the next RDSGroup chunk
                start += RDS_GROUP_LEN
                stop += RDS_GROUP_LEN
        except RDSIntegrityFailure as err:
            self.fail_test_case(f'Invalid RDS group bytes detected by RDSPICode(): {repr(err)}')
        except RDSPICodeMismatch as err:
            self.fail_test_case('RDSPICode() rejected the PI code of an RDS block in '
                                f'stream_bytes: {repr(err)}')
        except (TypeError, ValueError) as err:
            self.fail_test_case(f'Invalid input detected in stream_bytes: {repr(err)}')

    def run_test_exception(self, pi_code: bytes, stream_bytes: bytes, exception_type: Exception,
                           exception_msg: str, set_input: bool = True) -> None:
        """Common method calls for a test case expected to raise an exception.

        Args:
            pi_code: Sets the pi_code ctor argument input.  Must be valid input.  The RDSPICode
                ctor is effectively unit tested within the RDSPICode.verify_pi_code_integrity()
                unit tests.
                (See: test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_validate_integrity)
            stream_bytes: Any number of bytes to add to the RDSPICode object utilizing the
                add_bytes() method.  This argument's length *must* be valid (e.g., length must
                be a multiple of RDS_GROUP_LEN, must be valid RDSGroup, must be associated with
                pi_code).  RDSPICode.add_bytes() has its own dedicated unit tests.
            exception_type: An Exception type to expect (e.g., ValueError).
            exception_msg: A sub-string, empty or not, to look for in the raised Exception.
            set_input: [OPTIONAL] Indicates who calls set_test_input().  If True, this method
                will call self.set_test_input().  If False, the test author must call it.
        """
        if stream_bytes is not None:
            self.populate_test_object(pi_code=pi_code, stream_bytes=stream_bytes)
        else:
            self.create_test_obj(pi_code=pi_code)
        if set_input is True:
            self.set_test_input()  # This test case utilizes default arguments
        self.expect_exception(exception_type=exception_type, exception_msg=exception_msg)
        self.run_test()

    def run_test_return(self, pi_code: bytes, stream_bytes: bytes, exp_ret: str,
                        set_input: bool = True) -> None:
        """Common method calls for a test case expected to return.

        Args:
            pi_code: Sets the pi_code ctor argument input.  Must be valid input.  The RDSPICode
                ctor is effectively unit tested within the RDSPICode.verify_pi_code_integrity()
                unit tests.
                (See: test.unit_test.test_rds.test_rds_pi_code.test_rds_pi_code_validate_integrity)
            stream_bytes: Any number of bytes to add to the RDSPICode object utilizing the
                add_bytes() method.  This argument's length *must* be valid (e.g., length must
                be a multiple of RDS_GROUP_LEN, must be valid RDSGroup, must be associated with
                pi_code).  RDSPICode.add_bytes() has its own dedicated unit tests.
            exp_ret: The expected return from the method call.
            set_input: [OPTIONAL] Indicates who calls set_test_input().  If True, this method
                will call self.set_test_input().  If False, the test author must call it.
        """
        self.populate_test_object(pi_code=pi_code, stream_bytes=stream_bytes)
        if set_input is True:
            self.set_test_input()  # This test case utilizes default arguments
        self.expect_return(exp_ret)
        self.run_test()

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order


class NormalRDSPICodeGRTUnitTest(RDSPICodeGRTUnitTest):
    """Normal Test Cases."""

    def test_n01_valid_complete_radio_text_set(self):
        """Valid and complete set of all radio text offsets."""
        stream_bytes = self.GOOD_SET2_MSG02A
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        exp_ret = self.GOOD_SET2_RADIO_TEXT
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_n02_valid_complete_radio_text_set_plus_some(self):
        """Valid and complete set of all radio text offsets."""
        stream_bytes = self.GOOD_SET2_MSG02A + self.GOOD_SET1_MSG00A
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        exp_ret = self.GOOD_SET2_RADIO_TEXT
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_n03_no_radio_text(self):
        """Valid RDS groups for this PI Code, but no Group Type 02s.

        This counts as a normal test (normal usage) even if it's expected to raise and exception.
        I might refactor later to just return an empty string.
        """
        stream_bytes = self.GOOD_SET1_MSG00A
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        exp_except = RDSMsgGroupTypeMissing
        exp_msg = 'This RDSPICode does not contain any Message Type 02s'
        self.run_test_exception(pi_code, stream_bytes,
                                exception_type=exp_except, exception_msg=exp_msg)


class ErrorRDSPICodeGRTUnitTest(RDSPICodeGRTUnitTest):
    """Error Test Cases."""

    def test_e01_no_input_bytes(self):
        """No bytes were input, either by add_bytes() or add_rds_group()."""
        stream_bytes = None
        pi_code = self.GOOD_SET2_MSG02A[:RDS_BLOCK_DATA_LEN]
        exp_except = RDSMsgGroupTypeMissing
        exp_msg = 'This RDSPICode does not contain any Message Type 02s'
        self.run_test_exception(pi_code, stream_bytes,
                                exception_type=exp_except, exception_msg=exp_msg)

    def test_e02_bad_type_none(self):
        """Bad sanitize data type: None."""
        stream_bytes = None
        pi_code = self.GOOD_SET2_MSG02A[:RDS_BLOCK_DATA_LEN]
        sanitize = None
        exp_except = TypeError
        exp_msg = 'argument should have been of type'
        self.set_test_input(sanitize)
        self.run_test_exception(pi_code, stream_bytes,
                                exception_type=exp_except, exception_msg=exp_msg, set_input=False)

    def test_e03_bad_type_str(self):
        """Bad sanitize data type: string."""
        stream_bytes = None
        pi_code = self.GOOD_SET2_MSG02A[:RDS_BLOCK_DATA_LEN]
        sanitize = 'True'
        exp_except = TypeError
        exp_msg = 'argument should have been of type'
        self.set_test_input(sanitize)
        self.run_test_exception(pi_code, stream_bytes,
                                exception_type=exp_except, exception_msg=exp_msg, set_input=False)


class BoundaryRDSPICodeGRTUnitTest(RDSPICodeGRTUnitTest):
    """Boundary Test Cases."""

    def test_b01_double_valid_complete_radio_text_sets(self):
        """Valid and complete set of all radio text offsets x2 (AKA a long capture)."""
        num_captured = 2
        stream_bytes = self.GOOD_SET2_MSG02A * num_captured
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        exp_ret = self.GOOD_SET2_RADIO_TEXT * num_captured
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_b02_ten_valid_complete_radio_text_sets(self):
        """Valid and complete set of all radio text offsets x10 (AKA a long capture)."""
        num_captured = 10
        stream_bytes = self.GOOD_SET2_MSG02A * num_captured
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        exp_ret = self.GOOD_SET2_RADIO_TEXT * num_captured
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_b03_sanitize_several_carriage_returns(self):
        """Sanitize radio text with several non-printables: carriage return (0xD)."""
        num_captured = 10
        stream_bytes = self.GOOD_SET3_MSG02A * num_captured
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        sanitize = True
        exp_ret = (self.GOOD_SET3_RADIO_TEXT * num_captured).replace('\r', '.')
        self.set_test_input(sanitize)
        self.run_test_return(pi_code, stream_bytes, exp_ret, set_input=False)

    def test_b04_do_not_sanitize_carriage_returns(self):
        """Disable sanitize for radio text with several non-printables: carriage return (0xD)."""
        num_captured = 10
        stream_bytes = self.GOOD_SET3_MSG02A * num_captured
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        sanitize = False
        exp_ret = self.GOOD_SET3_RADIO_TEXT * num_captured
        self.set_test_input(sanitize)
        self.run_test_return(pi_code, stream_bytes, exp_ret, set_input=False)


class SpecialRDSPICodeGRTUnitTest(RDSPICodeGRTUnitTest):
    """Special Test Cases."""

    def test_s01_mix_and_match_group_types(self):
        """Valid, ordered, radio text offsets have other messages mixed in."""
        stream_bytes = self.GOOD_SET1_GRP01_MSG00_OFF00 + self.GOOD_SET2_GRP01_MSG02_OFF00 \
            + self.GOOD_SET2_GRP01_MSG02_OFF01 + self.GOOD_SET1_GRP02_MSG00_OFF01 \
            + self.GOOD_SET2_GRP01_MSG02_OFF02 + self.GOOD_SET1_GRP03_MSG00_OFF02 \
            + self.GOOD_SET2_GRP01_MSG02_OFF03 + self.GOOD_SET1_GRP04_MSG00_OFF03 \
            + self.GOOD_SET2_GRP01_MSG02_OFF04 + self.GOOD_SET2_GRP01_MSG02_OFF05 \
            + self.GOOD_SET2_GRP01_MSG02_OFF06 + self.GOOD_SET2_GRP01_MSG02_OFF07 \
            + self.GOOD_SET2_GRP01_MSG02_OFF08 + self.GOOD_SET2_GRP01_MSG02_OFF09 \
            + self.GOOD_SET2_GRP01_MSG02_OFF10 + self.GOOD_SET2_GRP01_MSG02_OFF11 \
            + self.GOOD_SET2_GRP01_MSG02_OFF12 + self.GOOD_SET2_GRP01_MSG02_OFF13 \
            + self.GOOD_SET2_GRP01_MSG02_OFF14 + self.GOOD_SET2_GRP01_MSG02_OFF15
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        exp_ret = self.GOOD_SET2_RADIO_TEXT
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_s02_missing_trailing_offsets(self):
        """Valid, ordered, radio text offsets missing a few trailing offsets."""
        missing = 9  # The number of RDS groups to remove
        stream_bytes = self.GOOD_SET2_MSG02A[:len(self.GOOD_SET2_MSG02A)-missing * RDS_GROUP_LEN]
        exp_ret = self.GOOD_SET2_RADIO_TEXT[:len(self.GOOD_SET2_RADIO_TEXT)-missing*4]
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_s03_missing_leading_offsets(self):
        """Valid, ordered, radio text offsets missing a few leading offsets."""
        missing = 8  # The number of RDS groups to remove
        stream_bytes = self.GOOD_SET2_MSG02A[missing * RDS_GROUP_LEN:]
        exp_ret = '?' * missing * 4 + self.GOOD_SET2_RADIO_TEXT[missing*4:]
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_s04_missing_middle_offsets(self):
        """Valid, ordered, radio text offsets missing a few offsets in the middle."""
        stream_bytes = self.GOOD_SET2_GRP01_MSG02_OFF00 + self.GOOD_SET2_GRP01_MSG02_OFF15
        exp_ret = self.GOOD_SET2_RADIO_TEXT[:4] + '?' * 14 * 4 \
            + self.GOOD_SET2_RADIO_TEXT[len(self.GOOD_SET2_RADIO_TEXT)-4:]
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_s05_missing_bookend_offsets(self):
        """Valid, ordered, radio text offsets missing a few leading and trailing offsets."""
        start_grp = 2  # The starting group to keep
        keeping = 5    # The number of RDS groups to remove
        stream_bytes = self.GOOD_SET2_MSG02A[start_grp * RDS_GROUP_LEN:
                                             (start_grp+keeping)*RDS_GROUP_LEN]
        exp_ret = '?' * start_grp * 4 \
                  + self.GOOD_SET2_RADIO_TEXT[start_grp*4:(start_grp+keeping)*4]
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_s06_out_of_order_offsets(self):
        """Valid radio text offsets that are out of order.

        Live captures show me that radio text messages should be in order, by offset.
        I should handle it that, the first time I receive an offset less than the last offset seen,
        I: A. truncate the previous string, B. prepend the new string with leading filler
        characters (e.g., '?'), C. append the new string.
        """
        stream_bytes = self.GOOD_SET2_GRP01_MSG02_OFF00 + self.GOOD_SET2_GRP01_MSG02_OFF01 \
            + self.GOOD_SET2_GRP01_MSG02_OFF02 + self.GOOD_SET2_GRP01_MSG02_OFF01
        exp_ret = 'KONO' + ' 101' + '.1 S' + '???? 101'
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_s07_duplicate_offsets(self):
        """Valid radio text offsets but they're the same.

        Live captures show me that radio text messages should be in order, by offset.
        Much the same as out-of-order offsets, I'll treat duplicate offsets as if a few got
        dropped.  I should handle it that, the first time I receive a duplicate offset,
        I: A. truncate the previous string, B. prepend the new string with leading filler
        characters (e.g., '?'), C. append the new string.
        """
        stream_bytes = self.GOOD_SET2_GRP01_MSG02_OFF00 + self.GOOD_SET2_GRP01_MSG02_OFF01 \
            + self.GOOD_SET2_GRP01_MSG02_OFF01
        exp_ret = 'KONO' + ' 101' + '???? 101'
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        self.run_test_return(pi_code, stream_bytes, exp_ret)

    def test_s08_sanitize_normal(self):
        """Use the sanitize feature on radio text missing non-printables."""
        stream_bytes = self.GOOD_SET2_MSG02A
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        sanitize = True
        exp_ret = self.GOOD_SET2_RADIO_TEXT
        self.set_test_input(sanitize)
        self.run_test_return(pi_code, stream_bytes, exp_ret, set_input=False)

    def test_s09_sanitize_carriage_returns(self):
        """Use the sanitize feature on radio text with non-printables: carriage return (0xD)."""
        stream_bytes = self.GOOD_SET3_MSG02A
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        sanitize = True
        exp_ret = self.GOOD_SET3_RADIO_TEXT.replace('\r', '.')
        self.set_test_input(sanitize)
        self.run_test_return(pi_code, stream_bytes, exp_ret, set_input=False)

    def test_s10_do_not_sanitize_carriage_returns(self):
        """Disable the sanitize feature on radio text with non-printables: carriage return (0xD)."""
        stream_bytes = self.GOOD_SET3_MSG02A
        pi_code = stream_bytes[:RDS_BLOCK_DATA_LEN]
        sanitize = False
        exp_ret = self.GOOD_SET3_RADIO_TEXT
        self.set_test_input(sanitize)
        self.run_test_return(pi_code, stream_bytes, exp_ret, set_input=False)


if __name__ == '__main__':
    execute_test_cases()
