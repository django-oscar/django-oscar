import os
from settings import *
import dj_database_url

DEBUG = True

OSCAR_SHOP_TAGLINE = 'SmallsLIVE'

TIME_ZONE = 'America/New_York'

LANGUAGE_CODE = 'en-us'

LANGUAGES = (
    ('en-us', 'English'),
    ('da', 'Danish'),
    ('de', 'German'),
    ('el', 'Greek'),
    ('en', 'English'),
    ('es', 'Spanish'),
    ('fr', 'French'),
    ('it', 'Italian'),
    ('ja', 'Japanese'),
    ('pl', 'Polish'),
    ('pt', 'Portugese'),
    ('ru', 'Russian'),
    ('sk', 'Slovakian'),
)

OSCAR_DEFAULT_CURRENCY = "USD"

ADMINS = (
    ('Nate Aune', 'nate@appsembler.com'),
)
EMAIL_SUBJECT_PREFIX = '[SmallsLIVE] '
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

SECRET_KEY = os.environ.get("SECRET_KEY", "herokudefault")

# Parse database configuration from $DATABASE_URL
DATABASES['default'] = dj_database_url.config()

# For south
SOUTH_DATABASE_ADAPTERS = {'default':'south.db.postgresql_psycopg2'}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

