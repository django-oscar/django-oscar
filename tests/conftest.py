import os
import warnings

import django


def pytest_addoption(parser):
    parser.addoption('--postgres', action='store_true')
    parser.addoption(
        '--deprecation', choices=['strict', 'log', 'none'], default='log')


def pytest_configure(config):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')

    deprecation = config.getoption('deprecation')
    if deprecation == 'strict':
        warnings.simplefilter('error', DeprecationWarning)
        warnings.simplefilter('error', PendingDeprecationWarning)
        warnings.simplefilter('error', RuntimeWarning)
    if deprecation == 'log':
        warnings.simplefilter('always', DeprecationWarning)
        warnings.simplefilter('always', PendingDeprecationWarning)
        warnings.simplefilter('always', RuntimeWarning)
    elif deprecation == 'none':
        # Deprecation warnings are ignored by default
        pass

    if config.getoption('postgres'):
        os.environ['DATABASE_ENGINE'] = 'django.db.backends.postgresql_psycopg2'
        os.environ['DATABASE_NAME'] = 'oscar'

    django.setup()
