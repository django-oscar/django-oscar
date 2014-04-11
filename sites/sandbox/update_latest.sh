#!/usr/bin/env bash

# Update to latest commit
cd /var/www/oscar/builds/latest
git pull --ff-only 2> /dev/null
[ $? -gt 0 ] && echo "Git pull failed" >&2 && exit 1

# Update any dependencies
source ../../virtualenvs/latest/bin/activate
python setup.py develop
pip install -r requirements.txt

# Update sandbox database
cd sites/sandbox
./manage.py syncdb --noinput
./manage.py migrate

# Rebuild statics
./manage.py collectstatic --noinput
./manage.py thumbnail clear

# Load standard fixtures
./manage.py loaddata ../_fixtures/promotions.json

# Restart Tomcat (to pick up any Solr schema changes)
/etc/init.d/tomcat7 restart

# Re-compile python code
touch deploy/wsgi/latest.wsgi

# Copy down server config files
cp deploy/nginx/latest.conf /etc/nginx/sites-enabled/latest.oscarcommerce.com
/etc/init.d/nginx configtest 2> /dev/null && /etc/init.d/nginx force-reload 2> /dev/null

cp deploy/supervisord/latest.conf /etc/supervisor/conf.d/latest.conf
supervisorctl reread && supervisorctl reload

# Copy down cronjob file
cp deploy/cron.d/oscar /etc/cron.d/oscar-latest
