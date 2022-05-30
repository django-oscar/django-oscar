from django import template
from django.apps import apps

register = template.Library()


@register.simple_tag(takes_context=True)
def get_parameters(context, except_field):
    """
    Renders current get parameters except for the specified parameter
    """
    getvars = context['request'].GET.copy()
    getvars.pop(except_field, None)
    if len(getvars.keys()) > 0:
        return "%s&" % getvars.urlencode()

    return ''


@register.tag
def if_app_installed(parser, token):
    nodelist = parser.parse(("end_if_app_installed",))
    try:
        tag_name, app_label = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(f"{token.contents.split()[0]} tag requires a single argument")
    if not (app_label[0] == app_label[-1] and app_label[0] in ('"', "'")):
        raise template.TemplateSyntaxError(f"{tag_name} tag's argument should be in quotes")
    parser.delete_first_token()
    return ConditionalOutputNode(nodelist, app_label[1:-1])


class ConditionalOutputNode(template.Node):
    def __init__(self, nodelist, app_label):
        self.nodelist = nodelist
        self.app_label = app_label

    def render(self, context):
        try:
            apps.get_app_config(self.app_label)
        except LookupError:
            return ''
        return self.nodelist.render(context)
