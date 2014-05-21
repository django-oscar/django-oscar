#!/usr/bin/env bash
# 
# Test migrations run correctly with MySQL and Postgres

# Fail if any command fails
# http://stackoverflow.com/questions/90418/exit-shell-script-based-on-process-exit-code
set -e
set -o pipefail

if [ ! "$TRAVIS" == "true" ]
then
  # If not on Travis, then create databases
  echo "Creating MySQL database and user"
  mysql -u root -e "DROP DATABASE IF EXISTS oscar_vagrant; CREATE DATABASE oscar_vagrant"
  mysql -u root -e "GRANT ALL PRIVILEGES ON oscar_vagrant.* TO 'travis'@'localhost' IDENTIFIED BY '';"

  echo "Creating Postgres database and user"
  psql -c "DROP ROLE IF EXISTS travis"
  psql -c "CREATE ROLE travis LOGIN PASSWORD ''"
  psql -c "DROP DATABASE IF EXISTS oscar_vagrant"
  psql -c "CREATE DATABASE oscar_vagrant"
fi

# MySQL
echo "Running migrations against MySQL"
./manage.py syncdb --noinput --settings=settings_mysql > /dev/null
./manage.py migrate --noinput --settings=settings_mysql

# Postgres
echo "Running migrations against Postgres"
./manage.py syncdb --noinput --settings=settings_postgres > /dev/null
./manage.py migrate --noinput --settings=settings_postgres
