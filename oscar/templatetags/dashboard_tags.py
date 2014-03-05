from django import template

from oscar.core.loading import get_class
Order = get_class('order.models', 'Order')
get_nodes = get_class('dashboard.menu', 'get_nodes')

register = template.Library()


def get_num_user_orders(parser, token):
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


register.tag('num_orders', get_num_user_orders)


def dashboard_navigation(parser, token):
    return DashboardNavigationNode()


class DashboardNavigationNode(template.Node):

    def render(self, context):
        context['nav_items'] = get_nodes(context['user'])
        return ''


register.tag('dashboard_navigation', dashboard_navigation)
