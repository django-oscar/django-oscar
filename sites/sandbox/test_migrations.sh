#!/usr/bin/env bash

# MySQL
mysql -u root --password=root_password -e "DROP DATABASE IF EXISTS oscar_vagrant; CREATE DATABASE oscar_vagrant"
./manage.py syncdb --noinput --settings=settings_mysql > /dev/null
./manage.py migrate --noinput --settings=settings_mysql

# Postgres
sudo -u postgres psql -c "DROP DATABASE IF EXISTS oscar_vagrant"
sudo -u postgres psql -c "CREATE DATABASE oscar_vagrant"
./manage.py syncdb --noinput --settings=settings_postgres > /dev/null
./manage.py migrate --noinput --settings=settings_postgres