from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'oscar_vagrant',
        'USER': 'travis',
        'PASSWORD': '',
        'HOST': '127.0.0.1',
        'PORT': '',
    }
}
