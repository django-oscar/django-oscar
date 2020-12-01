import django
from django import template
from django.template.base import TextNode

from oscar.core.compat import FormFieldNode

register = template.Library()


@register.tag
def annotate_form_field(parser, token):
    """
    Set an attribute on a form field with the widget type

    This means templates can use the widget type to render things differently
    if they want to. Until 3.1, Django did not make this available by default.
    """
    args = token.split_contents()
    if len(args) < 2:
        raise template.TemplateSyntaxError(
            "annotate_form_field tag requires a form field to be passed")
    if django.VERSION < (3, 1):
        return FormFieldNode(args[1])
    return TextNode('')
