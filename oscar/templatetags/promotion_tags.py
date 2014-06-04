from django.template import Library, Node, Variable, RequestContext
from django.template.loader import select_template


register = Library()


class PromotionNode(Node):
    def __init__(self, promotion):
        self.promotion_var = Variable(promotion)

    def render(self, context):
        promotion = self.promotion_var.resolve(context)
        template = select_template([promotion.template_name(),
                                    'promotions/default.html'])
        args = {'promotion': promotion}
        args.update(**promotion.template_context(request=context['request']))
        ctx = RequestContext(context['request'], args)
        return template.render(ctx)


@register.tag
def render_promotion(parser, token):
    __, promotion = token.split_contents()
    return PromotionNode(promotion)
