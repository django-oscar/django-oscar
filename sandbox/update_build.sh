#!/usr/bin/env

cd /var/www/oscar/django-oscar
git pull

# Update any dependencies
source ../env/bin/activate
python setup.py develop
pip install -r testing-reqs.txt

# Run any new migrations
cd sandbox
./manage.py syncdb --noinput
./manage.py migrate
./manage.py collectstatic

# Re-compile python code
touch deploy/wsgi/sandbox.wsgi