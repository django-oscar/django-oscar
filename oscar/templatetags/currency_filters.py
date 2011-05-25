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
    try:
        symbol = settings.CURRENCY_SYMBOL
        return "%s%s" % (symbol, locale.format("%.2f", value, grouping=True)) 
    except AttributeError:
        return locale.currency(value, symbol=True, grouping=True)
