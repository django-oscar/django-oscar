from django import template
from django.db.models import get_model
from django.conf import settings
Product = get_model('catalogue', 'product')

register = template.Library()


@register.tag(name="product_image")
def do_basket_form(parse, token):
    """
    Template tag for adding the product image data to the context
    """
    tokens = token.split_contents()
    if len(tokens) != 2 and len(tokens) != 4:
        raise template.TemplateSyntaxError("%r tag uses the following syntax: {%% product_image product_var [as variable_name] %%}" % tokens[0])
    product_var = tokens[1]
    context_key = tokens[3] if len(tokens) == 4 else 'image'
    return ProductImageNode(product_var, context_key)


class ProductImageNode(template.Node):
    def __init__(self, product_var, context_key):
        self.product_var = template.Variable(product_var)
        self.context_key = context_key
        
    def render(self, context):
        try:
            product = self.product_var.resolve(context)
        except template.VariableDoesNotExist:
            return ''
        images = product.images.all().order_by('display_order')
        if images.count():
            image = images[0]
        else:
            image = {'thumbnail_url': settings.OSCAR_MISSING_IMAGE_URL}
        context[self.context_key] = image
        return ''
