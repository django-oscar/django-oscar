from django import template

from oscar.core.loading import feature_hidden

register = template.Library()


@register.tag
def get_parameters(parser, token):
    """
    Renders the query parameters with the exception of the passed one

    Usage:

    .. code-block:: html+django

        <a href="?{% get_parameters key %}&key=1">...</a>

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``key``              The query param to ignore
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=get_parameters+path%3A%2Foscar%2Ftemplates&type=Code
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


@register.tag
def iffeature(parser, token):
    """
    Only renders the contained mark-up if the specified feature is enabled.

    Usage:

    .. code-block:: html+django

        {% iffeature feature_name %}
            ...
        {% endiffeature %}

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``feature_name``     The feature name to test for
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=get_parameters+path%3A%2Foscar%2Ftemplates&type=Code
    """
    nodelist = parser.parse(('endiffeature',))
    try:
        tag_name, app_name, = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0])
    if not (app_name[0] == app_name[-1] and app_name[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name)
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
            return ''
