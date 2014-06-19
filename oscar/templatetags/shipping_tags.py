from django import template


register = template.Library()


@register.tag
def shipping_charge(parse, token):
    """
    Injects the shipping charge into the template context:

    Usage:

    .. code-block:: html+django

        {% shipping_charge shipping_method basket as name %}
        Shipping charge is {{ name }}.

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``shipping_method``  The shipping method instance
    ``basket``           The basket instance to calculate shipping charges for
    ``name``             The variable name to assign the charge to
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=shipping_charge+path%3A%2Foscar%2Ftemplates&type=Code
    """
    return build_node(ShippingChargeNode, token)


@register.tag
def shipping_charge_discount(parse, token):
    """
    Injects the shipping discount into the template context:

    Usage:

    .. code-block:: html+django

        {% shipping_discount shipping_method basket as name %}
        Shipping discount is {{ charge }}.

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``shipping_method``  The shipping method instance
    ``basket``           The basket instance to calculate shipping charges for
    ``name``             The variable name to assign the charge to
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=shipping_discount+path%3A%2Foscar%2Ftemplates&type=Code
    """
    return build_node(ShippingChargeDiscountNode, token)


@register.tag
def shipping_charge_excl_discount(parse, token):
    """
    Injects the shipping charge with no discounts applied into the template
    context:

    Usage:

    .. code-block:: html+django

        {% shipping_charge_excl_discount shipping_method basket as name %}
        Shipping discount is {{ name }}.

    The arguments are:

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``shipping_method``  The shipping method instance
    ``basket``           The basket instance to calculate shipping charge for
    ``name``             The variable name to assign the charge to
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=shipping_charge_excl_discount+path%3A%2Foscar%2Ftemplates&type=Code
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
