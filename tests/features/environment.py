def before_all(context):
    from tests.config import configure
    configure()

    from django.test import utils
    utils.setup_test_environment()


def before_scenario(context, scenario):
    from django.db import connection
    connection.creation.create_test_db(verbosity=1, autoclobber=True)

    # Set-up webtest app
    from django_webtest import DjangoTestApp
    context.browser = DjangoTestApp()


def after_scenario(context, scenario):
    from django.db import connection
    connection.creation.destroy_test_db('', verbosity=1)


def after_all(context):
    from django.test import utils
    utils.teardown_test_environment()
