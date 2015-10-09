#!/usr/bin/env bash
#
# Run static analysis of the codebase
#
# This is run on Travis to ensure that pull requests conform to the project coding standards.
flake8 src/oscar/ || exit $?
isort -q --recursive --diff src/ || exit $?
