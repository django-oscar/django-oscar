from django import template

register = template.Library()


@register.simple_tag
def wishlists_containing_product(wishlists, product):
    return wishlists.filter(lines__product=product)
