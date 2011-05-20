"""
Special settings file for use when testing.  This specifies a SQLite 
database to use when running tests.

Just make sure you run the tests and specify this file:
> ./manage.py test --settings=settings_test
"""

from settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', 
        'NAME': ':memory:', 
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers':['null'],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': {
            'handlers': ['null'],
            'level': 'ERROR',
            'propagate': False,
        },
        'oscar.checkout': {
            'handlers': ['null'],
            'propagate': True,
            'level':'INFO',
        },
        'django.db.backends': {
            'handlers':['null'],
            'propagate': False,
            'level':'DEBUG',
        },
    }
}