#!/usr/bin/env bash

cd /var/www/oscar/builds/demo/
source ../../virtualenvs/demo/bin/activate
make demo

cd sites/demo
./manage.py thumbnail clear
./manage.py collectstatic --noinput

# Re-compile python code
touch deploy/wsgi/demo.wsgi

# Copy down server config files
cp deploy/nginx/demo.conf /etc/nginx/sites-enabled/demo.oscar.tangentlabs.co.uk
/etc/init.d/nginx configtest && /etc/init.d/nginx force-reload

cp deploy/apache2/demo.conf /etc/apache2/sites-enabled/demo.oscar.tangentlabs.co.uk
/etc/init.d/apache2 reload
