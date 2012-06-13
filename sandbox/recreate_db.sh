#!/bin/bash

DATABASE=db.sqlite

rm $DATABASE
./manage.py syncdb --noinput
./manage.py migrate

echo "Loading fixtures"
./manage.py loaddata countries.json

echo "Importing products"
./manage.py oscar_import_catalogue data/books-catalogue.csv

echo "Importing Images"
./manage.py oscar_import_catalogue_images data/books-images.tar.gz

echo "Creating superuser"
./manage.py createsuperuser --username=admin --email=admin@test.com
