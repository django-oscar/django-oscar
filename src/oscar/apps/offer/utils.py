from importlib import import_module

from django.core import exceptions
from django.urls import reverse

from oscar.apps.offer.applicator import Applicator  # backwards-compat  # noqa


def range_anchor(range):
    return u'<a href="%s">%s</a>' % (
        reverse('dashboard:range-update', kwargs={'pk': range.pk}),
        range.name)


def unit_price(offer, line):
    """
    Return the relevant price for a given basket line.

    This is required so offers can apply in circumstances where tax isn't known
    """
    return line.unit_effective_price


def load_proxy(proxy_class):
    module, classname = proxy_class.rsplit('.', 1)
    try:
        mod = import_module(module)
    except ImportError as e:
        raise exceptions.ImproperlyConfigured(
            "Error importing module %s: %s" % (module, e))
    try:
        return getattr(mod, classname)
    except AttributeError:
        raise exceptions.ImproperlyConfigured(
            "Module %s does not define a %s" % (module, classname))
