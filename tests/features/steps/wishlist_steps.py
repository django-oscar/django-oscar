from behave import *
from nose.tools import *


@given('they visit a product detail page')
def step(context):
    from oscar.test import factories
    context.product = factories.create_product()
    context.response = context.browser.get(
        context.product.get_absolute_url(), user=context.user)


@when('they click "Add to wishlist"')
def step(context):
    form = context.response.forms['add_to_wishlist_form']
    context.response = form.submit()


@then('a wishlist is created')
def step(context):
    eq_(1, context.user.wishlists.all().count())


@then('the product is in the wishlist')
def step(context):
    wishlist = context.user.wishlists.all()[0]
    ok_(context.product in [line.product for line in wishlist.lines.all()])
