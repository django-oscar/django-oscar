from behave import *
from nose.tools import *


@given('a user')
def step(context):
    from django_dynamic_fixture import G
    from oscar.core.compat import get_user_model
    User = get_user_model()
    context.user = G(User)


@given('an authenticated user')
def step(context):
    from django_dynamic_fixture import G
    from oscar.core.compat import get_user_model
    User = get_user_model()
    context.user = G(User)

    from django_webtest import DjangoTestApp
    #from django_webtest.compat import to_string
    #context.browser = DjangoTestApp(
    #    extra_environ={'WEBTEST_USER': to_string(context.user.username)})
