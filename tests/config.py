import os
import django

from django.conf import settings, global_settings
import oscar


def configure():
    if not settings.configured:
        from oscar.defaults import OSCAR_SETTINGS

        # Helper function to extract absolute path
        location = lambda x: os.path.join(
            os.path.dirname(os.path.realpath(__file__)), x)

        test_settings = {
            'DATABASES': {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                },
            },
            'INSTALLED_APPS': [
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'django.contrib.flatpages',
                'django.contrib.staticfiles',
                'sorl.thumbnail',
                'compressor',
                'tests._site.model_tests_app',  # contains models we need for testing

                # Use a custom partner app to test overriding models.  I can't
                # find a way of doing this on a per-test basis, so I'm using a
                # global change.
            ] + oscar.get_core_apps([
                'tests._site.apps.partner',
                'tests._site.apps.customer']),
            'TEMPLATE_CONTEXT_PROCESSORS': (
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.request",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.contrib.messages.context_processors.messages",
                'oscar.apps.search.context_processors.search_form',
                'oscar.apps.customer.notifications.context_processors.notifications',
                'oscar.apps.promotions.context_processors.promotions',
                'oscar.apps.checkout.context_processors.checkout',
                'oscar.core.context_processors.metadata',
            ),
            'TEMPLATE_DIRS': (
                location('templates'),
                oscar.OSCAR_MAIN_TEMPLATE_DIR,
            ),
            'TEMPLATE_LOADERS': (('django.template.loaders.cached.Loader',
                                     global_settings.TEMPLATE_LOADERS),),
            'MIDDLEWARE_CLASSES': global_settings.MIDDLEWARE_CLASSES + (
                'oscar.apps.basket.middleware.BasketMiddleware',
            ),
            'AUTHENTICATION_BACKENDS': (
                'oscar.apps.customer.auth_backends.EmailBackend',
                'django.contrib.auth.backends.ModelBackend',
            ),
            'HAYSTACK_CONNECTIONS': {
                'default': {
                    'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
                }
            },
            'PASSWORD_HASHERS': ['django.contrib.auth.hashers.MD5PasswordHasher'],
            'ROOT_URLCONF': 'tests._site.urls',
            'LOGIN_REDIRECT_URL': '/accounts/',
            'STATIC_URL': '/static/',
            'COMPRESS_ENABLED': False,
            'COMPRESS_ROOT': '',  # needed to avoid issue #1214
            'ADMINS': ('admin@example.com',),
            'DEBUG': False,
            'SITE_ID': 1,
            'USE_TZ': 1,
            'APPEND_SLASH': True,
            'DDF_DEFAULT_DATA_FIXTURE': 'tests.dynamic_fixtures.OscarDynamicDataFixtureClass',
            'SESSION_SERIALIZER': 'django.contrib.sessions.serializers.JSONSerializer',

            # temporary workaround for issue in sorl-thumbnail in Python 3
            # https://github.com/mariocesar/sorl-thumbnail/pull/254
            'THUMBNAIL_DEBUG': False,

            'OSCAR_INITIAL_ORDER_STATUS': 'A',
            'OSCAR_ORDER_STATUS_PIPELINE': {'A': ('B',), 'B': ()},
            'OSCAR_INITIAL_LINE_STATUS': 'a',
            'OSCAR_LINE_STATUS_PIPELINE': {'a': ('b', ), 'b': ()},
        }
        if django.VERSION >= (1, 5):
            test_settings['INSTALLED_APPS'] += ['tests._site.myauth', ]
            test_settings['AUTH_USER_MODEL'] = 'myauth.User'
        test_settings.update(OSCAR_SETTINGS)

        settings.configure(**test_settings)
