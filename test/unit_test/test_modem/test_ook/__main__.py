"""Defines the logic for running all modem.ook OOK() unit tests as a module.

    Typical usage example:

    python -m test.unit_test.test_modem.test_ook
"""

# Standard Imports
import sys
# Third Party Imports
# Local Imports
from test.loader import load_and_run


if __name__ == '__main__':
    # Run all test cases discovered in this package
    # Exit 0 on success, 1 otherwise
    sys.exit(not load_and_run('test/unit_test/test_modem/test_ook'))
