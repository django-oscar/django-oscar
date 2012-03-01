#!/bin/bash

DATABASE=db.sqlite

rm $DATABASE
./manage.py syncdb --noinput
./manage.py migrate
./manage.py oscar_import_catalogue data/books-catalogue.csv

echo "Creating superuser"
./manage.py createsuperuser --username=admin --email=admin@test.com