import os
import sys
import site

sys.stdout = sys.stderr

# Project root
root = '/var/www/oscar/django-oscar/sandbox/'
sys.path.insert(0, root)

# Packages from virtualenv
activate_this = '/var/www/oscar/env/bin/activate_this.py'
execfile(activate_this, dict(__file__=activate_this))

# Set environmental variable for Django and fire WSGI handler 
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import django.core.handlers.wsgi
_application = django.core.handlers.wsgi.WSGIHandler()

def application(environ, start_response):
    return _application(environ, start_response)
