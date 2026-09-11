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
TEST_DIR=test              # Directory containing the project test code
DEVOPS_DIR=devops          # Directory containing the devops scripts
# Directories containing the project source code
SOURCE_DIRS="gallant_input rxtx"


# PYLINT COMMANDS
# 1. Source Code
for SOURCE_DIR in $SOURCE_DIRS
do
    cd "$SOURCE_DIR"
    if [ $? -ne 0 ]
    then
        EXIT_CODE=1
    else
        echo "Running Pylint on $SOURCE_DIR"
        # find ./ -type f -name "*.py" -not -name "__init__.py" | xargs python -m pylint --score=no --disable=import-error
        find ./ -type f -name "*.py" -not -name "__init__.py" | xargs python -m pylint --score=no --disable=duplicate-code
        if [ $? -ne 0 ]
        then
            EXIT_CODE=1
        fi
    fi
    cd $ORIGINAL_DIRECTORY
done

# 2. Test Code
cd $TEST_DIR
if [ $? -ne 0 ]
then
    EXIT_CODE=1
else
    echo "Running Pylint on $TEST_DIR"
    find ./ -type f -name "*.py" -not -name "__init__.py" | xargs python -m pylint --score=no --disable=duplicate-code,too-many-ancestors,too-many-lines,wrong-import-order
    if [ $? -ne 0 ]
    then
        EXIT_CODE=1
    fi
fi
cd $ORIGINAL_DIRECTORY

# 3. Devops Scripts
# cd $DEVOPS_DIR
# if [ $? -ne 0 ]
# then
#     EXIT_CODE=1
# else
#     echo "Running Pylint on $DEVOPS_DIR"
#     # find ./ -type f -name "*.py" -not -name "__init__.py" | xargs python -m pylint --score=no --disable=import-error
#     find ./ -type f -name "*.py" -not -name "__init__.py" | xargs python -m pylint --score=no
#     if [ $? -ne 0 ]
#     then
#         EXIT_CODE=1
#     fi
# fi
# cd $ORIGINAL_DIRECTORY

# DONE
cd $ORIGINAL_DIRECTORY
echo ""
exit $EXIT_CODE
