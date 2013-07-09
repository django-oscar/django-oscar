#!/usr/bin/env bash

if [ "$TRAVIS" == "true" ]
then
  ROOT_PASSWORD=""
else
  ROOT_PASSWORD="root_password"
fi

# MySQL
mysql -u root --password=$ROOT_PASSWORD -e "DROP DATABASE IF EXISTS oscar_vagrant; CREATE DATABASE oscar_vagrant"
mysql -u root --password=$ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON oscar_vagrant.* TO 'oscar_user'@'%' IDENTIFIED BY 'oscar_password';"
./manage.py syncdb --noinput --settings=settings_mysql > /dev/null
./manage.py migrate --noinput --settings=settings_mysql

# Postgres
sudo -u postgres psql -c "DROP DATABASE IF EXISTS oscar_vagrant"
sudo -u postgres psql -c "CREATE DATABASE oscar_vagrant"
sudo -u postgres psql -c "DROP ROLE IF EXISTS oscar_user"
sudo -u postgres psql -c "CREATE ROLE oscar_user LOGIN PASSWORD 'oscar_password'"
./manage.py syncdb --noinput --settings=settings_postgres > /dev/null
./manage.py migrate --noinput --settings=settings_postgres