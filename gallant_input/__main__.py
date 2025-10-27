"""Entry point for package execution.

    Typical usage example:

    python -m gallant_input --help
"""

# Standard Imports
import sys
# Third Party Imports
# Local Imports
from gallant_input.main import main


if __name__ == '__main__':
    sys.exit(main())
