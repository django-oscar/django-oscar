from django import template


register = template.Library()


@register.tag
def shipping_charge(parse, token):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return build_node(ShippingChargeNode, token)


@register.tag
def shipping_charge_discount(parse, token):
    """
    Template tag for calculating the shipping discount for a given shipping
    method and basket, and injecting it into the template context.
    """
    return build_node(ShippingChargeDiscountNode, token)


@register.tag
def shipping_charge_excl_discount(parse, token):
    """
    Template tag for calculating the shipping charge (excluding discounts) for
    a given shipping method and basket, and injecting it into the template
    context.
    """
    return build_node(ShippingChargeExclDiscountNode, token)


def build_node(node_class, token):
    tokens = token.split_contents()
    if len(tokens) != 5 or tokens[3] != 'as':
        raise template.TemplateSyntaxError(
            "%(tag)r tag uses the following syntax: "
            "{%% %(tag)r method basket as "
            "name %%}" % {'tag': tokens[0]})

    method_var, basket_var, name_var = tokens[1], tokens[2], tokens[4]
    return node_class(method_var, basket_var, name_var)


class ShippingNode(template.Node):
    method_name = None

    def __init__(self, method_var, basket_var, name_var):
        self.method_var = template.Variable(method_var)
        self.basket_var = template.Variable(basket_var)
        self.name_var = name_var

    def render(self, context):
        try:
            method = self.method_var.resolve(context)
            basket = self.basket_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        context[self.name_var] = getattr(
            method, self.method_name)(basket)
        return ''


class ShippingChargeNode(ShippingNode):
    method_name = 'calculate'


class ShippingChargeDiscountNode(ShippingNode):
    method_name = 'discount'


class ShippingChargeExclDiscountNode(ShippingNode):
    method_name = 'calculate_excl_discount'
