from django import template

register = template.Library()


@register.tag
def annotate_form_field(parser, token):
    """
    Sets a ``widget_type`` attribute on a form field so templates can handle
    widgets differently.

    Usage:

    .. code-block:: html+django

        {% annotate_form_field field %}

        {% if field.widget_type == 'CheckboxInput %}
            ...
        {% endif %}

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``field``            The form field to annotate
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=annotate_form_field+path%3A%2Foscar%2Ftemplates&type=Code
    """
    args = token.split_contents()
    if len(args) < 2:
        raise template.TemplateSyntaxError(
            "annotate_form_field tag requires a form field to be passed")
    return FormFieldNode(args[1])


class FormFieldNode(template.Node):
    def __init__(self, field_str):
        self.field = template.Variable(field_str)

    def render(self, context):
        field = self.field.resolve(context)
        if hasattr(field, 'field'):
            field.widget_type = field.field.widget.__class__.__name__
        return ''
