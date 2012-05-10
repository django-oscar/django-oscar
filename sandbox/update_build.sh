#!/usr/bin/env bash

cd /var/www/oscar/django-oscar
git pull 2> /dev/null
[ $? -gt 0 ] && echo "Git pull failed" >&2 && exit 1

# Update any dependencies
source ../env/bin/activate
python setup.py develop
pip install -r requirements.txt

# Run any new migrations
cd sandbox
./manage.py syncdb --noinput
./manage.py migrate
./manage.py collectstatic --noinput

# Re-compile python code
touch deploy/wsgi/sandbox.wsgi