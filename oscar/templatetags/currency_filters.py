from decimal import Decimal as D, InvalidOperation

from django import template
from django.conf import settings
from babel.numbers import format_currency

register = template.Library()


@register.filter(name='currency')
def currency(value):
    """
    Format decimal value as currency
    """
    try:
        value = D(value)
    except (TypeError, InvalidOperation):
        return u""
    # Using Babel's currency formatting
    # http://packages.python.org/Babel/api/babel.numbers-module.html#format_currency
    kwargs = {
        'currency': settings.OSCAR_DEFAULT_CURRENCY,
        'format': getattr(settings, 'OSCAR_CURRENCY_FORMAT', None)}
    locale = getattr(settings, 'OSCAR_CURRENCY_LOCALE', None)
    if locale:
        kwargs['locale'] = locale
    return format_currency(value, **kwargs)
