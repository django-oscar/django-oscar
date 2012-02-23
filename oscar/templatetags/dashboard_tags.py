from django import template
from django.core.urlresolvers import reverse

from oscar.apps.order.models import Order


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
    try:
        tag_name, user = token.split_contents()
    except ValueError:
        raise template.TempalteSyntaxError("User required for dashboard navigation tag")
    return DashboardNavigationNode(user)


class DashboardNavigationNode(template.Node):
    def __init__(self, user):
        self.user = template.Variable(user)

    def render(self, context):
        # This needs to be made dynamic, using the user to filter
        self.items = []
        self.add_item('See statistics', 'dashboard:order-summary')
        self.add_item('Manage orders', 'dashboard:order-list')
        self.add_item('View reports', 'dashboard:reports-index')
        self.add_item('User management', 'dashboard:users-index')
        self.add_item('Content blocks', 'dashboard:promotion-list')
        self.add_item('Catalogue management', 'dashboard:catalogue-product-list')
        context['nav_items'] = self.items
        return ''

    def add_item(self, text, url_name):
        self.items.append({'text': text,
                           'url': reverse(url_name)})

register.tag('dashboard_navigation', dashboard_navigation)
