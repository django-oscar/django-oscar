from django import template
from django.core.urlresolvers import reverse

from oscar.apps.order.models import Order
from oscar.apps.dashboard.nav import get_nodes


def get_num_user_orders(parser, token):
    try:
        tag_name, user = token.split_contents()
        return NumUserOrdersNode(user)
    except IndexError:
        raise template.TemplateSyntaxError("%r tag requires a user as it's first argument" % tag_name)


class NumUserOrdersNode(template.Node):
    def __init__(self, user):
        self.user = template.Variable(user)

    def render(self, context):
        return Order.objects.filter(user=self.user.resolve(context)).count()


register = template.Library()
register.tag('num_orders', get_num_user_orders)


def dashboard_navigation(parser, token):
    return DashboardNavigationNode()


class DashboardNavigationNode(template.Node):

    def render(self, context):
        user = context['user']
        context['nav_items'] = get_nodes(user)
        return ''

    def asdf(sefl):

        # This needs to be made dynamic, using the user to filter
        self.add_item('See statistics', 'dashboard:order-summary')
        self.add_item('Manage orders', 'dashboard:order-list')
        self.add_item('View reports', 'dashboard:reports-index')
        self.add_item('User management', 'dashboard:users-index')
        self.add_item('Content blocks', 'dashboard:promotion-list')
        self.add_item('Catalogue management', 'dashboard:catalogue-product-list')
        context['nav_items'] = self.items
        return ''

register.tag('dashboard_navigation', dashboard_navigation)

