#!/usr/bin/env bash
#
# Rather verbose and destructive script to create both South migrations and the
# new native migrations (which we need as we support both Django 1.6 and 1.7).
# This will install and uninstall Django versions in your virtualenv, only work
# with the default SQLite database, destroy that database repeatedly

# Grab current version of Django from virtualenv
DJANGO_VERSION=$(pip freeze | awk 'BEGIN {FS="=="} /Django/ {print $2}')
SOUTH_VERSION=$(pip freeze | awk 'BEGIN {FS="=="} /South/ {print $2}')

APPS=( analytics checkout address shipping catalogue reviews partner basket payment \
       offer order customer promotions search voucher wishlists )

echo "Uninstalling Django(==$DJANGO_VERSION) and South(==$SOUTH_VERSION)"
pip uninstall Django South -y

echo "Generating Django-native (>=1.7) migrations"
# Commit of the stable/1.7.x branch that contains fix for https://code.djangoproject.com/ticket/23041,
# but doesn't suffer from https://code.djangoproject.com/ticket/23014
pip install https://github.com/django/django/archive/88135a8cf7d587b88e47f1223cf01c7698b52b74.zip
rm -f sites/sandbox/db.sqlite
sites/sandbox/manage.py migrate
sites/sandbox/manage.py makemigrations ${APPS[@]}

echo "Generating Django 1.6 migrations"
pip install "Django==1.6.5" "South==1.0"
rm -f sites/sandbox/db.sqlite
sites/sandbox/manage.py syncdb --noinput
sites/sandbox/manage.py migrate
for APP in "${APPS[@]}"
do
    sites/sandbox/manage.py schemamigration $APP --auto
done

echo "Restoring Django(==$DJANGO_VERSION) and South(==$SOUTH_VERSION)"
pip install "Django==$DJANGO_VERSION" "South==$SOUTH_VERSION"
