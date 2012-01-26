from django import template
from django.db.models import get_model

from oscar.core.loading import import_module
forms = import_module('basket.forms', ['AddToBasketForm'])
Product = get_model('catalogue', 'product')

register = template.Library()


@register.tag(name="basket_form")
def do_basket_form(parse, token):
    """
    Template tag for adding the add-to-basket form to the
    template context so it can be rendered.
    """
    tokens = token.split_contents()
    if len(tokens) < 4 or tokens[3] != 'as':
        raise template.TemplateSyntaxError("%r tag uses the following syntax: {%% basket_form basket_var product_var as form_var %%}" % tokens[0])
    
    basket_var, product_var, form_var = tokens[1], tokens[2], tokens[4]
    return BasketFormNode(basket_var, product_var, form_var)


class BasketFormNode(template.Node):
    def __init__(self, basket_var, product_var, form_var):
        self.basket_var = template.Variable(basket_var)
        self.product_var = template.Variable(product_var)
        self.form_var = form_var
        
    def render(self, context):
        try:
            basket = self.basket_var.resolve(context)
            product = self.product_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        
        if isinstance(product, Product):
            initial = {
                'product_id': product.id,
            }
            context[self.form_var] = forms.AddToBasketForm(basket, instance=product,initial=initial)
        return ''