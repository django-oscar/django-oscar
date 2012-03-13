import locale
from decimal import Decimal

from django import template
from django.conf import settings
from django.template.defaultfilters import floatformat


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
            return "%s%s" % (symbol, floatformat(value, 2))
        else:
            return floatformat(value, 2)
    except TypeError:
        return '' 
        
