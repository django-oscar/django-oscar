from django import template
from oscar.core.prices import render_price

register = template.Library()


@register.filter(name='currency')
def currency(value, currency=None):
    """
    Format decimal value as currency
    """
    return render_price(value, currency)
