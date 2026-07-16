import warnings

from django import template
from django.template.base import TextNode

from oscar.utils.deprecation import RemovedInOscar32Warning

register = template.Library()


@register.filter
def child_price_field(form, child_pk):
    field_name = f"price_{child_pk}"
    if field_name in form.fields:
        return form[field_name]
    return ""


# pylint: disable=unused-argument
@register.tag
def annotate_form_field(parser, token):
    """
    Used to set an attribute on a form field with the widget type. This is now
    done by Django itself.
    """
    warnings.warn(
        "The annotate_form_field template tag is deprecated and will be removed in the next version of django-oscar",
        RemovedInOscar32Warning,
        stacklevel=2,
    )
    return TextNode("")
