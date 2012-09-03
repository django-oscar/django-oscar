#!/usr/bin/env bash

cd /var/www/oscar/builds/demo/

# Update any dependencies
source ../../virtualenvs/demo/bin/activate
python setup.py develop
pip install -r requirements.txt

# Run any new migrations
cd sites/demo
./manage.py syncdb --noinput
./manage.py migrate
./manage.py collectstatic --noinput

# Re-compile python code
touch deploy/wsgi/demo.wsgi

# Copy down server config files
cp deploy/nginx/demo.conf /etc/nginx/sites-enabled/demo.oscar.tangentlabs.co.uk
/etc/init.d/nginx configtest && /etc/init.d/nginx force-reload

cp deploy/apache2/demo.conf /etc/apache2/sites-enabled/demo.oscar.tangentlabs.co.uk
/etc/init.d/apache2 reload