#!/usr/bin/env bash

cd /var/www/oscar/builds/sandbox
git pull --ff-only 2> /dev/null
[ $? -gt 0 ] && echo "Git pull failed" >&2 && exit 1

# Update any dependencies
source ../../virtualenvs/sandbox/bin/activate
python setup.py develop
pip install -r requirements.txt

cd sites/sandbox
./manage.py syncdb --noinput
./manage.py migrate
./manage.py collectstatic --noinput
./manage.py loaddata ../_fixtures/promotions.json
./manage.py thumbnail clear
./manage.py rebuild_index --noinput
chown -R www-data:www-data whoosh_index

# Re-compile python code
touch deploy/wsgi/sandbox.wsgi

# Copy down server config files
cp deploy/nginx/sandbox.conf /etc/nginx/sites-enabled/sandbox.oscar.tangentlabs.co.uk
/etc/init.d/nginx configtest 2> /dev/null && /etc/init.d/nginx force-reload 2> /dev/null

cp deploy/apache2/sandbox.conf /etc/apache2/sites-enabled/sandbox.oscar.tangentlabs.co.uk
/etc/init.d/apache2 reload > /dev/null

# Copy down cronjob file
cp deploy/cron.d/oscar /etc/cron.d/oscar-sandbox
