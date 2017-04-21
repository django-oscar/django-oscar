from django import template

from oscar.core.compat import assignment_tag

register = template.Library()


@assignment_tag(register)
def purchase_info_for_product(request, product):
    if product.is_parent:
        return request.strategy.fetch_for_parent(product)

    return request.strategy.fetch_for_product(product)


@assignment_tag(register)
def purchase_info_for_line(request, line):
    return request.strategy.fetch_for_line(line)
