from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def absolutize_url(domain, path):
    return '{schema}://{domain}{path}'.format(
        schema=getattr(settings, 'OSCAR_URL_SCHEMA', 'http'),
        domain=domain,
        path=path
    )
