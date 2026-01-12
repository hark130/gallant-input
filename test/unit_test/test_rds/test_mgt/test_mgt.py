"""Defines the root rds.mgt sub-package unit test class.

RDSMsgGrpTypeUnitTest is the parent class for all rds.mgt sub-package related unit test classes.

    Typical usage example:

    from my_module_to_test import my_function_to_test as my_function
    from test.unit_test.test_rds.test_mgt.test_mgt import RDSMsgGrpTypeUnitTest

    class RDSSomethingUnitTest(RDSMsgGrpTypeUnitTest):
        # Establish the local test (input/output) dirs
        def __init__(self, *args, **kwargs) -> None:
        # Default directory for input files
        self.test_input_dir = os.path.join(HERE, 'test_input')
        # Default directory for output files
        self.test_output_dir = os.path.join(HERE, 'test_output')

        # Child class must override this method
        def call_callable(self):
            return my_function(*self._args, **self._kwargs)

        # Child class must override this method
        def validate_return_value(self):
            self._validate_return_value(return_value=return_value)

        # This is your test case
        def test_stuff(self):
            self.set_test_input(1, 2)
            self.expect_return(3)
"""

# Standard Imports
# Third Party Imports
# Local Imports
from gallant_input.rds.exceptions import RDSIntegrityFailure
from gallant_input.rds.group import RDSGroup
from test.unit_test.test_rds.test_rds import RDSUnitTest


class RDSMsgGrpTypeUnitTest(RDSUnitTest):
    """Parent class for all rds.mgt sub-package specific unit tests.

    Inherit from this class, define necessary functionality for the function you're testing and
    be sure to override the following methods in your child class:
        call_callable()
        validate_return_value()

    Available features:
        See: help(TediousUnitTest)

    Attributes:
        built_rds_group:    # RDSGroup() object for this test case
        test_case_data:     # Stores data about the test case as a TestCaseData object
        test_input_dir:     # Default input directory (OPTIONAL)
        test_output_dir:    # Default output directory (OPTIONAL)
    """

    # GOOD BLOCK VALUES
    # GOOD GROUP 1: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "    "
    GOOD_GRP1_MSG00_BLOCK_A0 = bytes('00110110010110001000011011', 'utf-8')  # PICode
    GOOD_GRP1_MSG00_BLOCK_B0 = bytes('00000000111011001101011000', 'utf-8')  # Metadata
    GOOD_GRP1_MSG00_BLOCK_C0 = bytes('11100001100010001111100110', 'utf-8')  # Alt Freq (AF)
    GOOD_GRP1_MSG00_BLOCK_D0 = bytes('00100000001000000011011100', 'utf-8')  # Offset 0: "  "
    # GOOD GROUP 2: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO" Offset 0
    GOOD_GRP2_MSG00_BLOCK_A0 = bytes('00110110010110001000011011', 'utf-8')  # PICode
    GOOD_GRP2_MSG00_BLOCK_B0 = bytes('00000000111011001101011000', 'utf-8')  # Metadata
    GOOD_GRP2_MSG00_BLOCK_C0 = bytes('11100001100010001111100110', 'utf-8')  # Alt Freq (AF)
    GOOD_GRP2_MSG00_BLOCK_D0 = bytes('01001011010011111111001100', 'utf-8')  # Offset 0: "KO"
    # GOOD GROUP 3: KONO 101.1 FM Live Capture of Group Type 00A - Station Name "KONO"
    GOOD_GRP3_MSG00_BLOCK_A1 = bytes('00110110010110001000011011', 'utf-8')  # PICode
    GOOD_GRP3_MSG00_BLOCK_B1 = bytes('00000000111010010110111100', 'utf-8')  # Metadata
    GOOD_GRP3_MSG00_BLOCK_C1 = bytes('11100001100010001111100110', 'utf-8')  # Alt Freq (AF)
    GOOD_GRP3_MSG00_BLOCK_D1 = bytes('01001110010011110001100000', 'utf-8')  # Offset 1: "NO"

    # GOOD GROUP VALUES
    # KONO 101.1 FM Live Capture of Group Type 00A - Station Name
    # GOOD GROUP 1: Station Name "    " Offset 0 "  "
    GOOD_GROUP1_MSG00_OFF0 = GOOD_GRP1_MSG00_BLOCK_A0 + GOOD_GRP1_MSG00_BLOCK_B0 \
        + GOOD_GRP1_MSG00_BLOCK_C0 + GOOD_GRP1_MSG00_BLOCK_D0
    # GOOD GROUP 2: Station Name "KONO" Offset 0 "KO"
    GOOD_GROUP2_MSG00_OFF0 = GOOD_GRP2_MSG00_BLOCK_A0 + GOOD_GRP2_MSG00_BLOCK_B0 \
        + GOOD_GRP2_MSG00_BLOCK_C0 + GOOD_GRP2_MSG00_BLOCK_D0
    # GOOD GROUP 2: Station Name "KONO" Offset 1 "NO"
    GOOD_GROUP2_MSG00_OFF1 = GOOD_GRP3_MSG00_BLOCK_A1 + GOOD_GRP3_MSG00_BLOCK_B1 \
        + GOOD_GRP3_MSG00_BLOCK_C1 + GOOD_GRP3_MSG00_BLOCK_D1

    # CORE CLASS METHODS
    # Methods listed in call order

    def __init__(self, *args, **kwargs) -> None:
        """RDSBlockUnitTest ctor."""
        # ATTRIBUTES
        self.built_rds_group = None  # RDSGroup() object built from input

        super().__init__(*args, **kwargs)

    def call_callable(self):
        """Defines how the class will invoke the function call.

        Child class must override this method.  See TediousUnitTest.call_callable() for details.
        """
        # Example Usage:
        # return the_function_you_are_testing(*self._args, **self._kwargs)
        raise NotImplementedError(
            self._test_error.format('The child class must override the call_callable method with '
                                    'the function to test.'))

    def validate_return_value(self, return_value):
        """Defines how the class will validate the return value of the tested call.

        Child class must override this method.
        See TediousUnitTest.validate_return_value() for details.
        """
        # Example Usage:
        # self._validate_return_value(return_value=return_value)
        raise NotImplementedError(
            self._test_error.format('The child class must override the validate_return_value '
                                    'method with the appropriate validation logic'))

    # COMMON-USE METHODS
    # Methods listed in alphabetical order

    def build_rds_group(self, rds_group: bytes, assume_na: bool = True) -> None:
        """Build an RDSGroup() object to fetch RDSMsgGroupType()s with."""
        try:
            self.built_rds_group = RDSGroup(rds_group=rds_group, assume_na=assume_na)
            self.built_rds_group.verify_group_integrity()
        except (RDSIntegrityFailure, TypeError, ValueError) as err:
            self.fail_test_case(f'Invalid RDSGroup({rds_group}, {assume_na}) '
                                f'test case input: {repr(err)}')

    def set_ctor_args(self, rds_group: bytes, assume_na: bool) -> None:
        """Set the RDSGroup() ctor arguments.

        Args:
            rds_group: Sets the rds_group argument input.  Input should be valid and well-formed.
            assume_na: Sets the assume_na argument input.  Input should be valid and well-formed.
        """
        self.input_rds_group = rds_group
        self.input_assume_na = assume_na

    # CLASS HELPER METHODS
    # Methods listed in alphabetical order
