from django.template import Library, RequestContext
from django.template.loader import select_template

register = Library()


@register.simple_tag(takes_context=True)
def render_promotion(context, promotion):
    template = select_template([
        promotion.template_name(), 'promotions/default.html'])

    args = {
        'request': context['request'],
        'promotion': promotion
    }
    args.update(**promotion.template_context(request=context['request']))

    ctx = RequestContext(context['request'], args)
    return template.render(ctx)
