#!/usr/bin/env bash
#
# Test migrations run correctly

# Fail if any command fails
# http://stackoverflow.com/questions/90418/exit-shell-script-based-on-process-exit-code
set -e
set -o pipefail

# Postgres
echo "Running migrations against Postgres"
./manage.py migrate --noinput --settings=settings_postgres
