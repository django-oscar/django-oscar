from django import template
from django.template.loader import render_to_string, select_template


register = template.Library()


@register.simple_tag(takes_context=True)
def render_product(context, product):
    """
    Render a product snippet as you would see in a browsing display.

    This templatetag looks for different templates depending on the UPC and
    product class of the passed product.  This allows alternative templates to
    be used for different product classes.
    """
    names = ['catalogue/partials/product/upc-%s.html' % product.upc,
             'catalogue/partials/product/class-%s.html' % product.product_class.name.lower(),
             'catalogue/partials/product.html']
    template_ = select_template(names)
    # Ensure the passed product is in the context as 'product'
    context['product'] = product
    return template_.render(context)
