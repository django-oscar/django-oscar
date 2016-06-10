from decimal import Decimal as D
from decimal import InvalidOperation

from babel.numbers import format_currency
from django import template
from django.conf import settings
from django.utils.translation import get_language, to_locale

register = template.Library()


@register.filter(name='currency')
def currency(value, currency=None):
    """
    Format decimal value as currency
    """
    try:
        value = D(value)
    except (TypeError, InvalidOperation):
        return u""
    # Using Babel's currency formatting
    # http://babel.pocoo.org/en/latest/api/numbers.html#babel.numbers.format_currency
    kwargs = {
        'currency': (currency if not currency is None else
            settings.OSCAR_DEFAULT_CURRENCY),
        'format': getattr(settings, 'OSCAR_CURRENCY_FORMAT', None),
        'locale': to_locale(get_language() or settings.LANGUAGE_CODE),
        'currency_digits': getattr(settings, 'OSCAR_CURRENCY_DIGITS', True),
        'format_type': getattr(settings, 'OSCAR_CURRENCY_FORMAT_TYPE', 'standard'),
    }
    return format_currency(value, **kwargs)
