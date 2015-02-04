from settings import *

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

DEBUG_PROPAGATE_EXCEPTIONS = True

NOSE_ARGS = ['-s']

# Disable logging
import logging
logging.disable(logging.ERROR)

# Use proper cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
