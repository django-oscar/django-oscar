import os
from settings import *
import dj_database_url

SECRET_KEY = os.environ.get("SECRET_KEY", "herokudefault")

# Parse database configuration from $DATABASE_URL
DATABASES['default'] = dj_database_url.config()

# For south
SOUTH_DATABASE_ADAPTERS = {'default':'south.db.postgresql_psycopg2'}

# Honor the 'X-Forwarded-Proto' header for request.is_secure()
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Allow all host headers
ALLOWED_HOSTS = ['*']

