import locale

from django import template
from django.conf import settings

register = template.Library()


@register.filter(name='currency')
def currency(value):
    """
    Format decimal value as currency
    """
    try:
        locale.setlocale(locale.LC_ALL, settings.LOCALE)
    except AttributeError:
        locale.setlocale(locale.LC_ALL, '')

    # We allow the currency symbol to be overridden as the version in system
    # locales if often not the desired one.
    try:
        symbol = getattr(settings, 'CURRENCY_SYMBOL', None)
        if symbol:
            # A custom currency symbol is specified.  Check to see if a
            # custom format is specified too - this allows the position of the
            # currency symbol to be controlled.
            format = getattr(
                settings, 'CURRENCY_FORMAT', u"%(symbol)s%(value)s")
            return format % {
                'symbol': symbol,
                'value': locale.format("%.2f", value, grouping=True)}
        else:
            # Use locale's currency format
            c = locale.currency(value, symbol=True, grouping=True)
            return unicode(c, 'utf8')
    except TypeError:
        return ''
