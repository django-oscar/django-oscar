from django import template
from oscar.core.loading import get_model

from oscar.core.loading import get_class

AddToBasketForm = get_class('basket.forms', 'AddToBasketForm')
SimpleAddToBasketForm = get_class('basket.forms', 'SimpleAddToBasketForm')
Product = get_model('catalogue', 'product')

register = template.Library()

QNT_SINGLE, QNT_MULTIPLE = 'single', 'multiple'


@register.tag(name="basket_form")
def do_basket_form(parse, token):
    """
    Template tag for adding the add-to-basket form to the
    template context so it can be rendered.
    """
    tokens = token.split_contents()
    if len(tokens) < 4 or tokens[3] != 'as':
        raise template.TemplateSyntaxError(
            "%r tag uses the following syntax: "
            "{%% basket_form request product_var as "
            "form_var %%}" % tokens[0])

    request_var, product_var, form_var = tokens[1], tokens[2], tokens[4]

    quantity_type = tokens[5] if len(tokens) == 6 else QNT_MULTIPLE
    if quantity_type not in (QNT_SINGLE, QNT_MULTIPLE):
        raise template.TemplateSyntaxError(
            "%r tag only accepts the following quantity types: "
            "'single', 'multiple'" % tokens[0])
    return BasketFormNode(request_var, product_var, form_var, quantity_type)


class BasketFormNode(template.Node):
    def __init__(self, request_var, product_var, form_var, quantity_type):
        self.request_var = template.Variable(request_var)
        self.product_var = template.Variable(product_var)
        self.form_var = form_var
        self.form_class = (AddToBasketForm if quantity_type == QNT_MULTIPLE
                           else SimpleAddToBasketForm)

    def render(self, context):
        try:
            request = self.request_var.resolve(context)
            product = self.product_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''

        if not isinstance(product, Product):
            return ''

        initial = {}
        if not product.is_group:
            initial['product_id'] = product.id
        form = self.form_class(
            request, instance=product, initial=initial)

        context[self.form_var] = form
        return ''
