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
cp deploy/nginx/demo.conf /etc/nginx/sites-enabled/demo.oscarcommerce.com
/etc/init.d/nginx configtest && /etc/init.d/nginx force-reload

cp deploy/supervisord/demo.conf /etc/supervisor/conf.d/demo.conf
supervisorctl reread && supervisorctl reload
