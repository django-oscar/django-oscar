from django import template

from oscar.core.loading import get_class

Order = get_class('order.models', 'Order')
get_nodes = get_class('dashboard.menu', 'get_nodes')

register = template.Library()


@register.tag
def num_orders(parser, token):
    """
    Renders the number of orders a given user has placed.

    Usage:

    .. code-block:: html+django

        Number of orders placed: {% num_orders user %}

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``user``             The user instance
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=num_orders+path%3A%2Foscar%2Ftemplates&type=Code
    """
    try:
        tag_name, user = token.split_contents()
        return NumUserOrdersNode(user)
    except IndexError:
        raise template.TemplateSyntaxError(
            "%r tag requires a user as it's first argument" % tag_name)


class NumUserOrdersNode(template.Node):
    def __init__(self, user):
        self.user = template.Variable(user)

    def render(self, context):
        return Order.objects.filter(user=self.user.resolve(context)).count()


@register.tag
def dashboard_navigation(parser, token):
    """
    Injects the dashboard navigation nodes into the template context using name
    ``nav_items``

    Usage:

    .. code-block:: html+django

        {% dashboard_navigation user %}

        <ul>
            {% for item in nav_items %}
            <li>
                {% if item.is_heading %}
                    ...
                {% else %}
                    ...
                {% endif %}
            </li>
        </ul>

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``user``             The user instance
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=dashboard_navigation+path%3A%2Foscar%2Ftemplates&type=Code
    """
    return DashboardNavigationNode()


class DashboardNavigationNode(template.Node):

    def render(self, context):
        context['nav_items'] = get_nodes(context['user'])
        return ''
