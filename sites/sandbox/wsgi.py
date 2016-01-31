# isort:skip
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

from django.core.wsgi import get_wsgi_application  # isort:skip
from whitenoise.django import DjangoWhiteNoise  # isort:skip


application = get_wsgi_application()
application = DjangoWhiteNoise(application)
