from django import template


register = template.Library()


@register.tag
def wishlists_containing_product(parse, token):
    """
    Inject the wishlists that contain a given product into the template context.

    Usage:

    .. code-block:: html+django

        {% wishlists_containing_product wishlists product as name %}

    ===================  =====================================================
    Argument             Description
    ===================  =====================================================
    ``wishlists``        An iterable of wishlist instances.
    ``product``          The product to test for.
    ``name``             The variable name to assign to
    ===================  =====================================================

    `Example usage in Oscar's templates`__

    __ https://github.com/tangentlabs/django-oscar/search?q=wishlists_containing_product+path%3A%2Foscar%2Ftemplates&type=Code
    """
    tokens = token.split_contents()
    if len(tokens) != 5:
        raise template.TemplateSyntaxError(
            "%r tag uses the following syntax: "
            "{%% wishlists_containing_product wishlists product as "
            "ctx_var %%}" % tokens[0])

    wishlists_var, product_var, name_var = tokens[1], tokens[2], tokens[4]
    return ProductWishlistsNode(
        wishlists_var, product_var, name_var)


class ProductWishlistsNode(template.Node):
    def __init__(self, wishlists_var, product_var, name_var):
        self.wishlists_var = template.Variable(wishlists_var)
        self.product_var = template.Variable(product_var)
        self.name_var = name_var

    def render(self, context):
        try:
            wishlists = self.wishlists_var.resolve(context)
            product = self.product_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        context[self.name_var] = wishlists.filter(
            lines__product=product)
        return ''
