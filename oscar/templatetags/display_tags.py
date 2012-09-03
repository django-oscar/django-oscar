from django import template

register = template.Library()


def get_parameters(parser, token):
    """
    {% get_parameters except_field %}
    """

    args = token.split_contents()
    if len(args) < 2:
        raise template.TemplateSyntaxError(
            "get_parameters tag takes at least 1 argument")
    return GetParametersNode(args[1].strip())


class GetParametersNode(template.Node):
    """
    Renders current get parameters except for the specified parameter
    """
    def __init__(self, field):
        self.field = field

    def render(self, context):
        request = context['request']
        getvars = request.GET.copy()

        if self.field in getvars:
            del getvars[self.field]

        if len(getvars.keys()) > 0:
            get_params = "%s&" % getvars.urlencode()
        else:
            get_params = ''

        return get_params

get_parameters = register.tag(get_parameters)
