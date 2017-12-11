from django import template


register = template.Library()


@register.simple_tag
def purchase_info_for_product(request, product):
    if product.is_parent:
        return request.strategy.fetch_for_parent(product)

    return request.strategy.fetch_for_product(product)


@register.simple_tag
def purchase_info_for_line(request, line):
    return request.strategy.fetch_for_line(line)
