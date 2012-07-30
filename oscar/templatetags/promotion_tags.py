from copy import copy

from django.template import Library, Node, Variable, TemplateSyntaxError
from django.template.loader import select_template


register = Library()


class PromotionNode(Node):
    def __init__(self, promotion):
        self.promotion_var = Variable(promotion)

    def render(self, context):
        promotion = self.promotion_var.resolve(context)
        template = select_template([promotion.template_name(),
                                    'promotions/default.html'])
        ctx = copy(context)
        ctx['promotion'] = promotion
        ctx.update(promotion.template_context(request=context['request']))
        return template.render(ctx)


@register.tag('render_promotion')
def get_promotion_html(parser, token):
    try:
        __, promotion = token.split_contents()
    except ValueError:
        raise TemplateSyntaxError(
            "%r expects promotion instance as required argument",
            token.split_contents()[0]
        )
    return PromotionNode(promotion)
