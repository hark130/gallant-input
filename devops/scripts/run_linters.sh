#!/bin/sh

# This script was made to help automate and standardize how Pylint is executed on the code base.
# This script will execute all commands regardless of how many fail and exit with a non-zero value.
#
# This script uses the following exit codes:
#   0 on success
#   1 if any Pylint command exits with a non-zero value or an expected directory is missing


# GLOBAL VARIABLES
EXIT_CODE=0                # Value to exit with
ORIGINAL_DIRECTORY=$(pwd)  # Current working directory


# LINTER COMMANDS
# 1. Pycodestyle
echo "Running Pycodestyle"
# pycodestyle --max-line-length=100 ./
pycodestyle --max-line-length=100 --exclude=digital_filters.py,filter_examples.py,iq_io_example.py,moving_average_filter.py,digitization.py,fsk_example.py,pysdr_pulse_shaping.py,pysdr_*.py,simple_symbol_sync.py,costas_loop.py,rotate_poc.py,shmelstone_*.py ./
if [ $? -ne 0 ]
then
    echo "*** Pycodestyle Failed ***"
    EXIT_CODE=1
fi
cd $ORIGINAL_DIRECTORY

# 2. Pylint
./devops/scripts/run_pylint.sh
if [ $? -ne 0 ]
then
    echo "*** Pylint Failed ***"
    EXIT_CODE=1
fi
cd $ORIGINAL_DIRECTORY

# DONE
cd $ORIGINAL_DIRECTORY
if [ $EXIT_CODE -ne 0 ]
then
    echo "*** A Linter Failed ***"
fi
echo ""
exit $EXIT_CODE
