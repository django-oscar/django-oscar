import os
import sys
import site
import urllib

sys.stdout = sys.stderr

# Project root
root = '/var/www/oscar/builds/latest/sites/sandbox'
sys.path.insert(0, root)

# Packages from virtualenv
activate_this = '/var/www/oscar/virtualenvs/latest/bin/activate_this.py'
with open(activate_this) as f:
    code = compile(f.read(), activate_this, 'exec')
    exec(code, dict(__file__=activate_this))

# Set environmental variable for Django and fire WSGI handler
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
if sys.platform != "win32":
    os.environ['PYTHON_EGG_CACHE'] = '/tmp/.python-eggs'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
