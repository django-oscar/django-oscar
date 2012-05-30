#!/usr/bin/env bash

cd /var/www/oscar/builds/qa/

# Update any dependencies
source ../../virtualenvs/qa/bin/activate
python setup.py develop
pip install -r requirements.txt

# Run any new migrations
cd sandbox
./manage.py syncdb --noinput
./manage.py migrate
./manage.py collectstatic --noinput

# Re-compile python code
touch deploy/wsgi/qa.wsgi

# Copy down server config files
cp deploy/nginx/qa.conf /etc/nginx/sites-enabled/qa.oscar.tangentlabs.co.uk
/etc/init.d/nginx configtest && /etc/init.d/nginx force-reload

cp deploy/apache2/qa.conf /etc/apache2/sites-enabled/qa.oscar.tangentlabs.co.uk
/etc/init.d/apache2 reload