from django import template

from oscar.core.loading import get_class
get_nodes = get_class('dashboard.menu', 'get_nodes')

register = template.Library()


def dashboard_navigation(parser, token):
    return DashboardNavigationNode()


class DashboardNavigationNode(template.Node):

    def render(self, context):
        context['nav_items'] = get_nodes(context['user'])
        return ''


register.tag('dashboard_navigation', dashboard_navigation)
