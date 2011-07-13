from django import template
from django.db.models import get_model

from oscar.apps.basket.forms import AddToBasketForm
register = template.Library()
product_model = get_model('catalogue', 'product')

@register.tag(name="basket_form")
def do_basket_form(parse, token):
    tokens = token.split_contents()
    
    if len(tokens) < 3 or tokens[2] != 'as':
        raise template.TemplateSyntaxError("%r tag uses the following syntax: {% basket_form product_var as form_var %}" % tokens[0])
    
    product_var = tokens[1]
    form_var = tokens[3]
    
    return BasketFormNode(product_var, form_var)


class BasketFormNode(template.Node):
    def __init__(self, product_var, form_var):
        self.product_var = template.Variable(product_var)
        self.form_var = form_var
        
    def render(self, context):
        try:
            product = self.product_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        
        if isinstance(product, product_model):
            initial = {
                'product_id': product.id,
            }
            context[self.form_var] = AddToBasketForm(instance=product,initial=initial)
        return ''