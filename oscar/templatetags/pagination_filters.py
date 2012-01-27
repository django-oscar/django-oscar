from django import template

register = template.Library()

@register.filter(name='change_page')
def change_page(request, page_num):
    u"""Return next/prev page URL with search params and page number included"""
    params = request.GET.copy()
    params['page'] = page_num
    return params.urlencode()
