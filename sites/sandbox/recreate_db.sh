#!/bin/bash

DATABASE=db.sqlite

rm $DATABASE
./manage.py syncdb --noinput
./manage.py migrate

echo "Loading fixtures"
./manage.py loaddata countries.json ../_fixtures/pages.json

echo "Importing products"
./manage.py oscar_import_catalogue ../_fixtures/books-catalogue.csv

echo "Importing Images"
./manage.py oscar_import_catalogue_images ../_fixtures/books-images.tar.gz

echo "Creating superuser"
./manage.py createsuperuser --username=admin --email=admin@test.com
