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
    loc = locale.localeconv()
    try:
        return locale.currency(value, loc['currency_symbol'], grouping=True)
    except TypeError:
        return ''