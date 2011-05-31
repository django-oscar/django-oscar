import locale
from decimal import Decimal

from django import template
from django.conf import settings

register = template.Library()

@register.filter(name='currency')
def currency(value):
    u"""Return value converted to a locale currency"""
    try:
        locale.setlocale(locale.LC_ALL, settings.LOCALE)
    except AttributeError:
        locale.setlocale(locale.LC_ALL, '')
        
    # We allow the currency symbol to be overridden    
    symbol = getattr(settings, 'CURRENCY_SYMBOL', None)
    try:
        if symbol:
            return "%s%s" % (symbol, locale.format("%.2f", value, grouping=True))
        else:
            return locale.currency(value, symbol=True, grouping=True)
    except TypeError:
        return '' 
        
