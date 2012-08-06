import locale

from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='currency')
def currency(value):
    """
    Return value converted to a locale currency
    """
    try:
        locale.setlocale(locale.LC_ALL, settings.LOCALE)
    except AttributeError:
        locale.setlocale(locale.LC_ALL, '')

    # We allow the currency symbol to be overridden
    symbol = getattr(settings, 'CURRENCY_SYMBOL', None)
    try:
        if symbol:
            return u"%s%s" % (symbol, locale.format("%.2f", value, grouping=True))
        else:
            c = locale.currency(value, symbol=True, grouping=True)
            return unicode(c, 'utf8')
    except TypeError:
        return ''

