from django import template

from oscar.core.loading import feature_hidden

register = template.Library()


@register.simple_tag(takes_context=True)
def get_parameters(context, except_field):
    """
    Renders current get parameters except for the specified parameter
    """
    getvars = context["request"].GET.copy()
    getvars.pop(except_field, None)
    if len(getvars.keys()) > 0:
        return "%s&" % getvars.urlencode()

    return ""


@register.tag()
def iffeature(parser, token):
    nodelist = parser.parse(("endiffeature",))
    try:
        (
            tag_name,
            app_name,
        ) = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    if not (app_name[0] == app_name[-1] and app_name[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name
        )
    parser.delete_first_token()
    return ConditionalOutputNode(nodelist, app_name[1:-1])


class ConditionalOutputNode(template.Node):
    def __init__(self, nodelist, feature_name):
        self.nodelist = nodelist
        self.feature_name = feature_name

    def render(self, context):
        if not feature_hidden(self.feature_name):
            output = self.nodelist.render(context)
            return output
        else:
            return ""
