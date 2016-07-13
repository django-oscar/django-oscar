import os
import django


def pytest_addoption(parser):
    parser.addoption('--postgres', action='store_true')


def pytest_configure(config):
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.settings')

    if config.getoption('postgres'):
        os.environ['DATABASE_ENGINE'] = 'django.db.backends.postgresql_psycopg2'
        os.environ['DATABASE_NAME'] = 'oscar'

    django.setup()
