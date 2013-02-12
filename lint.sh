#!/bin/bash

dir=$(dirname $0)
package=pyramid_addons

# flake8 (runs pep8 and pyflakes)
flake8 $dir/$package
if [ $? -ne 0 ]; then
    echo "Exiting due to flake8 errors. Fix and re-run to finish tests."
    exit $?
fi

# pylint
output=$(pylint --rcfile=$dir/.pylintrc $dir/$package 2> /dev/null)
if [ -n "$output" ]; then
    echo "--pylint--"
    echo -e "$output"
fi

# pep 257
find $dir/$package -name [A-Za-z_]\*.py | xargs pep257
exit $?
