from django import template

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