from django import template

register = template.Library()

from .currency_filters import render_currency


@register.simple_tag()
def currency(value, currency=None):
    """
    Render a price in currency notation
    """
    return render_currency(value, currency)
