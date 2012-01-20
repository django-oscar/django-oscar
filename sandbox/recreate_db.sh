#!/bin/bash

DATABASE=db.sqlite

rm $DATABASE
./manage.py syncdb --noinput
./manage.py createsuperuser --username=admin --email=admin@test.com