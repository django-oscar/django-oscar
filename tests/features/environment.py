def before_all(context):
    from tests.config import configure
    configure()

    from django.test import utils
    utils.setup_test_environment()


def before_scenario(context, scenario):
    from django.db import connection
    connection.creation.create_test_db(verbosity=0, autoclobber=True)

    # Set-up webtest app

    # Ensure settings are patched just like in django_webtest
    from django.conf import settings

    # Copied from django_webtest
    context._cached_middleware = settings.MIDDLEWARE_CLASSES
    context._cached_auth_backends = settings.AUTHENTICATION_BACKENDS

    webtest_auth_middleware = 'django_webtest.middleware.WebtestUserMiddleware'
    django_auth_middleware = 'django.contrib.auth.middleware.AuthenticationMiddleware'

    settings.MIDDLEWARE_CLASSES = list(settings.MIDDLEWARE_CLASSES)
    if django_auth_middleware not in settings.MIDDLEWARE_CLASSES:
        # There can be a custom AuthenticationMiddleware subclass or
        # replacement, we can't compute its index so just put our auth
        # middleware to the end.  If appending causes problems
        # _setup_auth_middleware method can be overriden by a subclass.
        settings.MIDDLEWARE_CLASSES.append(webtest_auth_middleware)
    else:
        index = settings.MIDDLEWARE_CLASSES.index(django_auth_middleware)
        settings.MIDDLEWARE_CLASSES.insert(index + 1, webtest_auth_middleware)

    settings.AUTHENTICATION_BACKENDS = list(settings.AUTHENTICATION_BACKENDS)
    backend_name = 'django_webtest.backends.WebtestUserBackend'
    settings.AUTHENTICATION_BACKENDS.insert(0, backend_name)

    from django_webtest import DjangoTestApp
    context.browser = DjangoTestApp()


def after_scenario(context, scenario):
    from django.db import connection
    connection.creation.destroy_test_db('', verbosity=0)

    from django.conf import settings
    settings.MIDDLEWARE_CLASSES = context._cached_middleware
    settings.AUTHENTICATION_BACKENDS = context._cached_auth_backends


def after_all(context):
    from django.test import utils
    utils.teardown_test_environment()
