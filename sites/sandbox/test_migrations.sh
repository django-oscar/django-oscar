#!/usr/bin/env bash

# fail if any command fails
# http://stackoverflow.com/questions/90418/exit-shell-script-based-on-process-exit-code
set -e
set -o pipefail

if [ ! "$TRAVIS" == "true" ]
then
  mysql -u root --password="root_password" -e "DROP DATABASE IF EXISTS oscar_vagrant; CREATE DATABASE oscar_vagrant"
  mysql -u root --password="root_password" -e "GRANT ALL PRIVILEGES ON oscar_vagrant.* TO 'travis'@'%' IDENTIFIED BY '';"

  sudo -u postgres psql -c "DROP ROLE IF EXISTS travis"
  sudo -u postgres psql -c "CREATE ROLE travis LOGIN PASSWORD ''"
  sudo -u postgres psql -c "DROP DATABASE IF EXISTS oscar_vagrant"
  sudo -u postgres psql -c "CREATE DATABASE oscar_vagrant"
fi

# MySQL
./manage.py syncdb --noinput --settings=settings_mysql > /dev/null
./manage.py migrate --noinput --settings=settings_mysql

# Postgres
./manage.py syncdb --noinput --settings=settings_postgres > /dev/null
./manage.py migrate --noinput --settings=settings_postgres