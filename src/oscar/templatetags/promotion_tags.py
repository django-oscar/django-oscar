from django.template import Library
from django.template.loader import select_template

register = Library()


@register.simple_tag(takes_context=True)
def render_promotion(context, promotion):
    template = select_template([
        promotion.template_name(), 'promotions/default.html'])
    request = context['request']

    ctx = {
        'request': request,
        'promotion': promotion
    }
    ctx.update(**promotion.template_context(request=request))

    return template.render(ctx, request)
