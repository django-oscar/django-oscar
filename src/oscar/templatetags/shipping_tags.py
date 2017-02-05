from django import template

from oscar.core.compat import assignment_tag

register = template.Library()


@assignment_tag(register)
def shipping_charge(method, basket):
    """
    Template tag for calculating the shipping charge for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.calculate(basket)


@assignment_tag(register)
def shipping_charge_discount(method, basket):
    """
    Template tag for calculating the shipping discount for a given shipping
    method and basket, and injecting it into the template context.
    """
    return method.discount(basket)


@assignment_tag(register)
def shipping_charge_excl_discount(method, basket):
    """
    Template tag for calculating the shipping charge (excluding discounts) for
    a given shipping method and basket, and injecting it into the template
    context.
    """
    return method.calculate_excl_discount(basket)
