from django import template
from django.conf import settings
from babel.numbers import format_currency

register = template.Library()


@register.simple_tag()
def currency(value, currency=''):
    """
    Render a price in currency notation
    """
    if not currency:
        currency = settings.OSCAR_DEFAULT_CURRENCY
    kwargs = {'currency': currency}
    locale = getattr(settings, 'OSCAR_CURRENCY_LOCALE', None)
    if locale:
        kwargs['locale'] = locale
    return format_currency(value, **kwargs)
