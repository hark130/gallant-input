"""Defines the TestCaseData class.

Provides a dataclass to store information pertaining to unit tests deriving from
unittest.case.TestCase.
The TestCaseData class members are set to frozen making them immutable once assigned.

Typically this will be used in a root class inheriting from tediousstart ie TediousFuncTest.

    Typical usage example:

    test_case_data = TestCaseData.generate_from_id(self.id())

    self.id() => 'test_normal.PreToolFuncTestNormal.test_n30_usecase_2_assemble_verbose'

    test_case_data.name          => 'Normal_030'
    test_case_data.number        => 30
    test_case_data.number_padded => '030'
    test_case_data.nebs_category => 'Normal'
    test_case_data.package       => 'PreToolFuncTestNormal'
    test_case_data.description   => 'usecase 2 assemble verbose'
"""

# Standard Imports
from dataclasses import dataclass
from enum import Enum
from re import findall, split
from typing import Dict, Final, TypeVar
# Third Party Imports
from hobo.validation import validate_string, validate_type
# Local Imports


class NebsCategory(Enum):
    """NEBS Category Enumeration.

    Provides a const like structure to access the nebs names as strings.
    """
    NORMAL = 'Normal'
    ERROR = 'Error'
    BOUNDARY = 'Boundary'
    SPECIAL = 'Special'


# Lookup for converting single letter nebs to full nebs name.
NEBS_DICTIONARY: Final[Dict] = {'n': NebsCategory.NORMAL, 'e': NebsCategory.ERROR,
                                'b': NebsCategory.BOUNDARY, 's': NebsCategory.SPECIAL}

# Define a TypeVar to represent the TestCaseData data class (for the purposes of type hints)
TestCaseDataObj = TypeVar("TestCaseDataObj", bound="TestCaseData")


@dataclass(frozen=True)
class TestCaseData():
    """Data class holding unittest.case.TestCase details.

    Use the generate_from_id() class method to construct a TestCaseData object.

    Defines a collection of attributes to manage and organize test case information.
    Once set the attributes are immutable.

    Attributes:
        name:          Test case name in the format: 'Normal_01'
        number:        Test case number as an integer
        number_padded: Test case number as a string and padded with '0's
        nebs_category: Test case full nebs name ie 'Boundary'
        package:       The package this test belongs to ie 'PreToolFuncTestNormal'
        description:   The test description with '_' replaced with spaces
    """

    name: str = ''
    number: int = 0
    number_padded: str = ''
    nebs_category: str = ''
    package: str = ''
    description: str = ''

    def __post_init__(self) -> None:
        """Post-construction validation.

        Performs type validation of all attributes.
        TestCaseData objects should be created with the generate_from_id() class method.

        Raises:
            TypeError: Non-integer assigned to number attribute.
            ValueError: Non-string, empty string or test number invalid.
        """

        validate_string(self.name, 'name')
        validate_type(self.number, 'number', int)
        validate_string(self.number_padded, 'number_padded')
        validate_string(self.nebs_category, 'nebs_category')
        validate_string(self.package, 'package')
        validate_string(self.description, 'description')

        if self.number < 1:
            raise ValueError(f'Unsupported test number: {self.number}')

        if int(self.number_padded) != self.number:
            raise ValueError(f'"{self.number_padded}" does not match {self.number}')

    @classmethod
    def generate_from_id(cls, test_case_id: str) -> TestCaseDataObj:
        """Builds a new TestCaseData object from unittest.case.TestCase.id().

        Parses and validates test case method. Test case format example from TestCase.id():
            'test_normal.PreToolFuncTestNormal.test_n05_usecase_2_assemble_verbose'

        Args:
            test_case_id: Formatted string from TestCase.id().

        Returns:
            TestCaseData object.

        Raises:
            KeyError: The nebs character is not n, e, b, or s.
            TypeError: Incorrect type, int for number and string for the other attributes.
            ValueError: Supplied test_case_id did not match the correct format.
        """
        # LOCAL VARIABLES
        test_number_padded = cls._parse_test_case_number(test_case_id)
        test_package = cls._parse_test_case_package(test_case_id)
        test_description = cls._parse_test_case_description(test_case_id)
        test_nebs_category = cls._parse_test_case_nebs(test_case_id)
        test_name = '_'.join([test_nebs_category.value, test_number_padded])

        # GENERATE IT
        try:
            test_number = int(test_number_padded)
        except ValueError as err:
            raise ValueError(f'{test_number_padded} is not an integer.') from err

        # DONE
        return TestCaseData(name=test_name,
                            number=test_number,
                            number_padded=test_number_padded,
                            nebs_category=test_nebs_category.value,
                            package=test_package,
                            description=test_description)

    @classmethod
    def _parse_test_case_description(cls, test_case_id: str) -> str:
        """Parses the test description from unittest.case.TestCase.id().

        Parses and validates test case description.

        Args:
            test_case_id: Formatted string from TestCase.id().

        Returns:
            Test case description with '_' replaced with spaces.

        Raises:
            ValueError: Supplied test_case_id did not match the correct format.
        """
        result = split(r'(?<=test_[nebs])\d+_', test_case_id)

        if len(result) < 2:
            raise ValueError(f'Invalid test case format: {test_case_id}')

        return result[1].replace('_', ' ')

    @classmethod
    def _parse_test_case_nebs(cls, test_case_id: str) -> NebsCategory:
        """Parses the test nebs from unittest.case.TestCase.id().

        Parses and validates test case nebs.

        Args:
            test_case_id: Formatted string from TestCase.id().

        Returns:
            NebsCategory Enum matching the test cases nebs.

        Raises:
            ValueError: Supplied test_case_id did not match the correct format.
        """
        result = findall(r'(?<=test_)[nebs]', test_case_id)

        if len(result) < 1:
            raise ValueError(f'Invalid test case format: {test_case_id}')

        try:
            nebs_category = NEBS_DICTIONARY[result[0]]
        except KeyError as err:
            raise KeyError(f'Invalid test case format (nebs category): {result[0]}') from err

        return nebs_category

    @classmethod
    def _parse_test_case_number(cls, test_case_id: str) -> str:
        """Parses the test number from unittest.case.TestCase.id().

        Parses and validates test case number.

        Args:
            test_case_id: Formatted string from TestCase.id().

        Returns:
            Test case number with leading '0' padding as a string.

        Raises:
            ValueError: Supplied test_case_id did not match the correct format.
        """
        result = findall(r'(?<=test_[nebs])\d+', test_case_id)

        if len(result) < 1:
            raise ValueError(f'Invalid test case format (test number): {test_case_id}')

        return result[0]

    @classmethod
    def _parse_test_case_package(cls, test_case_id: str) -> str:
        """Parses the test package from unittest.case.TestCase.id().

        Parses and validates test case package.

        Args:
            test_case_id: Formatted string from TestCase.id().

        Returns:
            Test case package that the test originated from as a string ie 'PreToolFuncTestNormal'.

        Raises:
            ValueError: Supplied test_case_id did not match the correct format.
        """
        result = test_case_id.rsplit('.', -1)

        if len(result) < 2:
            raise ValueError(f'Invalid test case format: {test_case_id}')

        return result[1]
