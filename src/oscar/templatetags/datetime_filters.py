from django import template

from oscar.core.utils import format_timedelta

register = template.Library()


@register.filter
def timedelta(td):
    """
    Return formatted timedelta value
    """
    return format_timedelta(td)
