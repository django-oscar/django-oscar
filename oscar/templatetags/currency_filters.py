from decimal import Decimal as D, InvalidOperation

from django import template
from django.conf import settings
from django.utils.translation import to_locale, get_language
from babel.numbers import format_currency

register = template.Library()


@register.filter
def currency(value, currency=None):
    """
    Format a decimal value as a currency

    For example:

    .. code-block:: html+django

        {{ total|currency:"GBP" }}

    or using the core :class:`~oscar.core.prices.Price` class:

    .. code-block:: html+django

        {{ price.incl_tax|currency:price.currency }}

    If the arg is committed, then the currency is taken from the
    ``OSCAR_DEFAULT_CURRENCY`` setting.

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=currency+path%3A%2Foscar%2Ftemplates&type=Code
    """
    try:
        value = D(value)
    except (TypeError, InvalidOperation):
        return u""
    # Using Babel's currency formatting
    # http://babel.pocoo.org/docs/api/numbers/#babel.numbers.format_currency
    kwargs = {
        'currency': currency if currency else settings.OSCAR_DEFAULT_CURRENCY,
        'format': getattr(settings, 'OSCAR_CURRENCY_FORMAT', None),
        'locale': to_locale(get_language()),
    }
    return format_currency(value, **kwargs)
