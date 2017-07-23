#!/bin/bash
#
# Run the build mode specified by the BUILD variable, defined in
# .travis.yml. When the variable is unset, assume we should run the
# standard test suite.

# Show the commands being run.
set -x

# Exit on any error.
set -e

case "$BUILD" in
    docs)
        python setup.py build_sphinx;;
    linter)
        flake8;;
    *)
        python setup.py test --coverage --slowest --testr-args='';
        coverage report --show-missing;;
esac
