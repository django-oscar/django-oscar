#!/usr/bin/env bash
#
# Rather verbose and destructive script to create both South migrations and
# the new native migrations. This will install and uninstall Django versions
# in your virtualenv, only work with the default SQLite database, destroy that
# database repeatedly

pip uninstall Django South -y

# Commit of the stable/1.7.x branch that contains fix for https://code.djangoproject.com/ticket/23041
pip install https://github.com/django/django/archive/2c6ef625ad73c38769f086733356e37a938b69c3.zip
rm -f sites/sandbox/db.sqlite
sites/sandbox/manage.py migrate
sites/sandbox/manage.py makemigrations analytics checkout address shipping catalogue reviews partner basket payment offer order customer promotions search voucher wishlists

pip uninstall Django -y
pip install Django==1.6.5 South==1.0
rm -f sites/sandbox/db.sqlite
sites/sandbox/manage.py syncdb --noinput
sites/sandbox/manage.py migrate
sites/sandbox/manage.py schemamigration analytics --auto
sites/sandbox/manage.py schemamigration checkout --auto
sites/sandbox/manage.py schemamigration address --auto
sites/sandbox/manage.py schemamigration shipping --auto
sites/sandbox/manage.py schemamigration catalogue --auto
sites/sandbox/manage.py schemamigration reviews --auto
sites/sandbox/manage.py schemamigration partner --auto
sites/sandbox/manage.py schemamigration basket --auto
sites/sandbox/manage.py schemamigration payment --auto
sites/sandbox/manage.py schemamigration offer --auto
sites/sandbox/manage.py schemamigration order --auto
sites/sandbox/manage.py schemamigration customer --auto
sites/sandbox/manage.py schemamigration promotions --auto
sites/sandbox/manage.py schemamigration search --auto
sites/sandbox/manage.py schemamigration voucher --auto
sites/sandbox/manage.py schemamigration wishlists --auto

pip uninstall Django -y
