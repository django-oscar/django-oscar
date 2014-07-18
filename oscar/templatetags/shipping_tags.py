from django import template


register = template.Library()


@register.assignment_tag
def shipping_charge(method, basket):
    return method.calculate(basket)


@register.assignment_tag
def shipping_charge_discount(method, basket):
    return method.discount(basket)


@register.assignment_tag
def shipping_charge_excl_discount(method, basket):
    return method.calculate_excl_discount(basket)
