#!/bin/bash
#
# Run the sphinx build when enabled by the SPHINX environment variable.

if [[ ! -z "$SPHINX" ]]
then
    python setup.py build_sphinx
    exit $?
fi
exit $?
