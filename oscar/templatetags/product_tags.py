from django import template
from django.template.loader import select_template


register = template.Library()


@register.simple_tag(takes_context=True)
def render_product(context, product):
    """
    Render a product HTML snippet for inclusion in a browsing page (like search
    results or category browsing).

    This template used depends on the UPC and product class of the passed
    product.  This allows alternative templates to be used for different
    product classes.

    Usage:

    .. code-block:: html+django

        {% render_product product %}

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``product``          The product instance to render
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=render_product+path%3A%2Foscar%2Ftemplates&type=Code

    """
    if not product:
        # Search index is returning products that don't exist in the
        # database...
        return ''

    names = ['catalogue/partials/product/upc-%s.html' % product.upc,
             'catalogue/partials/product/class-%s.html'
             % product.get_product_class().slug,
             'catalogue/partials/product.html']
    template_ = select_template(names)
    # Ensure the passed product is in the context as 'product'
    context['product'] = product
    return template_.render(context)
