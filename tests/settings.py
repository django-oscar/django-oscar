import os

from oscar.defaults import *  # noqa

# Path helper
location = lambda x: os.path.join(
    os.path.dirname(os.path.realpath(__file__)), x)

ALLOWED_HOSTS = ['test', '.oscarcommerce.com']

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DATABASE_ENGINE',
                                 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DATABASE_NAME', 'oscar'),
        'USER': os.environ.get('DATABASE_USER', None),
        'PASSWORD': os.environ.get('DATABASE_USER', None),
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'django.contrib.flatpages',

    'oscar',
    'oscar.apps.analytics',
    'oscar.apps.checkout',
    'oscar.apps.address',
    'oscar.apps.shipping',
    'oscar.apps.catalogue',
    'oscar.apps.catalogue.reviews',
    'oscar.apps.partner',
    'oscar.apps.basket',
    'oscar.apps.payment',
    'oscar.apps.offer',
    'oscar.apps.order',
    'oscar.apps.customer',
    'oscar.apps.search',
    'oscar.apps.voucher',
    'oscar.apps.wishlists',
    'oscar.apps.dashboard',
    'oscar.apps.dashboard.reports',
    'oscar.apps.dashboard.users',
    'oscar.apps.dashboard.orders',
    'oscar.apps.dashboard.catalogue',
    'oscar.apps.dashboard.offers',
    'oscar.apps.dashboard.partners',
    'oscar.apps.dashboard.pages',
    'oscar.apps.dashboard.ranges',
    'oscar.apps.dashboard.reviews',
    'oscar.apps.dashboard.vouchers',
    'oscar.apps.dashboard.communications',
    'oscar.apps.dashboard.shipping',

    # 3rd-party apps that oscar depends on
    'widget_tweaks',
    'haystack',
    'treebeard',
    'sorl.thumbnail',
    'easy_thumbnails',
    'django_tables2',

    # Contains models we need for testing
    'tests._site.model_tests_app',
    'tests._site.myauth',
]

# Use a custom partner app to test overriding models. I can't find a way of
# doing this on a per-test basis, so I'm using a global change.
INSTALLED_APPS[INSTALLED_APPS.index('oscar.apps.partner')] = 'tests._site.apps.partner'
INSTALLED_APPS[INSTALLED_APPS.index('oscar.apps.customer')] = 'tests._site.apps.customer'
INSTALLED_APPS[INSTALLED_APPS.index('oscar.apps.catalogue')] = 'tests._site.apps.catalogue'
INSTALLED_APPS[INSTALLED_APPS.index('oscar.apps.dashboard')] = 'tests._site.apps.dashboard'

AUTH_USER_MODEL = 'myauth.User'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            location('_site/templates'),
        ],
        'OPTIONS': {
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.request',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',

                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.customer.notifications.context_processors.notifications',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ]
        }
    }
]


MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'oscar.apps.basket.middleware.BasketMiddleware',
]


AUTHENTICATION_BACKENDS = (
    'oscar.apps.customer.auth_backends.EmailBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

HAYSTACK_CONNECTIONS = {'default': {'ENGINE': 'haystack.backends.simple_backend.SimpleEngine'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
ROOT_URLCONF = 'tests._site.urls'
LOGIN_REDIRECT_URL = '/accounts/'
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
PUBLIC_ROOT = location('public')
MEDIA_ROOT = os.path.join(PUBLIC_ROOT, 'media')
DEBUG = False
SITE_ID = 1
USE_TZ = 1
APPEND_SLASH = True
DDF_DEFAULT_DATA_FIXTURE = 'tests.dynamic_fixtures.OscarDynamicDataFixtureClass'
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'
LANGUAGE_CODE = 'en-gb'

OSCAR_INITIAL_ORDER_STATUS = 'A'
OSCAR_ORDER_STATUS_PIPELINE = {'A': ('B',), 'B': ()}
OSCAR_INITIAL_LINE_STATUS = 'a'
OSCAR_LINE_STATUS_PIPELINE = {'a': ('b', ), 'b': ()}

SECRET_KEY = 'notverysecret'
TEST_RUNNER = 'django.test.runner.DiscoverRunner'
FIXTURE_DIRS = [location('unit/fixtures')]
