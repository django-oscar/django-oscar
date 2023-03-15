from settings import *  # noqa

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'oscar_travis',
        'USER': 'travis',
        'PASSWORD': 'travis',
        'HOST': '127.0.0.1',
        'PORT': '5432',
    }
}
