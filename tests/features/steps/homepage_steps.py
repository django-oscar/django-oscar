from behave import *
from nose.tools import *


@when('I view the homepage')
def step(context):
    br = context.browser
    context.response = br.get('/')


@when('I view a silly page')
def step(context):
    br = context.browser
    context.response = br.get('/silly/', status='*')


@then('I get a {code} response')
def step(context, code):
    eq_(int(code), context.response.status_code,
        "Response did not return a %s code" % code)


@then('page includes "{text}"')
def step(context, text):
    ok_(text.encode('utf8') in context.response.content.decode('utf8'),
        "%r not page content" % text)
