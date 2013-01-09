import os

from django.conf import settings, global_settings
from oscar import OSCAR_CORE_APPS, OSCAR_MAIN_TEMPLATE_DIR


def configure(nose_args=None):
    if not settings.configured:
        from oscar.defaults import OSCAR_SETTINGS

        # Helper function to extract absolute path
        location = lambda x: os.path.join(os.path.dirname(os.path.realpath(__file__)), x)

        settings.configure(
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                    }
                },
            INSTALLED_APPS=[
                'django.contrib.auth',
                'django.contrib.admin',
                'django.contrib.contenttypes',
                'django.contrib.sessions',
                'django.contrib.sites',
                'django.contrib.flatpages',
                'sorl.thumbnail',
                'compressor',
                ] + OSCAR_CORE_APPS,
            TEMPLATE_CONTEXT_PROCESSORS=(
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
                ),
            TEMPLATE_DIRS=(
                location('templates'),
                OSCAR_MAIN_TEMPLATE_DIR,
                ),
            MIDDLEWARE_CLASSES=global_settings.MIDDLEWARE_CLASSES + (
                'oscar.apps.basket.middleware.BasketMiddleware',
                ),
            AUTHENTICATION_BACKENDS=(
                'oscar.apps.customer.auth_backends.Emailbackend',
                'django.contrib.auth.backends.ModelBackend',
                ),
            HAYSTACK_CONNECTIONS={
                'default': {
                    'ENGINE': 'haystack.backends.simple_backend.SimpleEngine',
                }
            },
            PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'],
            ROOT_URLCONF='tests._site.urls',
            LOGIN_REDIRECT_URL='/accounts/',
            STATIC_URL='/static/',
            COMPRESS_ENABLED=False,
            DEBUG=False,
            SITE_ID=1,
            APPEND_SLASH=True,
            NOSE_ARGS=nose_args,
            **OSCAR_SETTINGS
        )
