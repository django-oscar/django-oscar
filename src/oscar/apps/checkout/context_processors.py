from __future__ import unicode_literals

from django.conf import settings


def checkout(request):
    anon_checkout_allowed \
        = getattr(settings, 'OSCAR_ALLOW_ANON_CHECKOUT', False)
    return {'anon_checkout_allowed': anon_checkout_allowed}
