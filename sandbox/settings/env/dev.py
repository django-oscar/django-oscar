from ..oscarsandbox import *  # pylint:disable=W0401,W0614

try:
    from oscarsandbox.json import *  # pylint:disable=W0401,W0614,E0611,E0401
except ModuleNotFoundError:
    pass

DEBUG = False
STATIC_ROOT = "/srv/www/oscarsandbox/static/"
STATICFILES_DIRS = tuple()

MEDIA_ROOT = "/srv/www/oscarsandbox/media/"

ALLOWED_HOSTS = ["*"]

# Force mail to console
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
