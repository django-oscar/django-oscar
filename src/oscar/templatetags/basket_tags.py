from django import template
from django.contrib.sessions.serializers import JSONSerializer

from oscar.core.loading import get_class, get_model

AddToBasketForm = get_class('basket.forms', 'AddToBasketForm')
SimpleAddToBasketForm = get_class('basket.forms', 'SimpleAddToBasketForm')
Product = get_model('catalogue', 'product')

register = template.Library()

QNT_SINGLE, QNT_MULTIPLE = 'single', 'multiple'


@register.simple_tag
def basket_form(request, product, quantity_type='single'):
    if not isinstance(product, Product):
        return ''

    initial = {}
    if not product.is_parent:
        initial['product_id'] = product.id

    form_class = AddToBasketForm
    if quantity_type == QNT_SINGLE:
        form_class = SimpleAddToBasketForm

    basket_post_data = request.session.pop("add_to_basket_form_post_data_%s" % product.pk, None)

    if basket_post_data is not None:
        basket_post_data = JSONSerializer().loads(basket_post_data.encode("latin-1"))

    form = form_class(request.basket, data=basket_post_data, product=product, initial=initial)

    return form
