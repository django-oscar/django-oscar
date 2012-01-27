#!/usr/bin/env python
import sys
import os
from optparse import OptionParser

from django.conf import settings, global_settings

if not settings.configured:
    from oscar.defaults import *
    oscar_settings = dict([(k, v) for k, v in locals().items() if k.startswith('OSCAR_')])

    # Helper function to extract absolute path
    location = lambda x: os.path.join(os.path.dirname(os.path.realpath(__file__)), x)

    settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    }
                },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                # Oscar apps
                'oscar',
                'oscar.apps.analytics',
                'oscar.apps.discount',
                'oscar.apps.order',
                'oscar.apps.checkout',
                'oscar.apps.shipping',
                'oscar.apps.catalogue',
                'oscar.apps.catalogue.reviews',
                'oscar.apps.basket',
                'oscar.apps.payment',
                'oscar.apps.offer',
                'oscar.apps.address',
                'oscar.apps.partner',
                'oscar.apps.customer',
                'oscar.apps.promotions',
                'oscar.apps.search',
                'oscar.apps.voucher',
                'oscar.apps.dashboard',
                'oscar.apps.dashboard.reports',
                ],
            TEMPLATE_CONTEXT_PROCESSORS=(
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.request",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.promotions.context_processors.promotions',
                'oscar.apps.checkout.context_processors.checkout',
                ),
            TEMPLATE_DIRS=(
                location('tests/templates'),
                ),
            MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES + (
                'oscar.apps.basket.middleware.BasketMiddleware',
                ),
            AUTHENTICATION_BACKENDS=(
                'oscar.apps.customer.auth_backends.Emailbackend',
                'django.contrib.auth.backends.ModelBackend',
                ),
            ROOT_URLCONF='tests.urls',
            LOGIN_REDIRECT_URL='/accounts/',
            DEBUG=False,
            SITE_ID=1,
            HAYSTACK_SEARCH_ENGINE='dummy',
            HAYSTACK_SITECONF = 'oscar.search_sites',
            **oscar_settings
        )

from django.test.simple import DjangoTestSuiteRunner


def run_tests(*test_args):
    # Modify path
    parent = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, parent)

    # Run tests
    test_runner = DjangoTestSuiteRunner(verbosity=1)
    if not test_args:
        test_args = ['oscar']
    failures = test_runner.run_tests(test_args)
    sys.exit(failures)

if __name__ == '__main__':
    parser = OptionParser()
    (options, args) = parser.parse_args()
    run_tests(*args)
