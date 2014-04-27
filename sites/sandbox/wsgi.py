"""
WSGI config for Heroku project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/howto/deployment/wsgi/
"""

import os, sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/.' )
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/..' )

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sandbox.settings_heroku")

from django.core.wsgi import get_wsgi_application
from dj_static import Cling, MediaCling

application = Cling(MediaCling(get_wsgi_application()))


