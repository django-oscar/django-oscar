from oscar.apps.shipping.methods import NoShippingRequired
from oscar.apps.shipping.repository import Repository as CoreRepository

from . import methods

METHODS = (
    methods.Standard(),
    methods.Express(),
)


class Repository(CoreRepository):

    def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
        return self.prime_methods(basket, METHODS)

    def find_by_code(self, code, basket):
        if code == NoShippingRequired.code:
            method = NoShippingRequired()
        else:
            method = None
            for method_ in METHODS:
                if method_.code == code:
                    method = method_
            if method is None:
                raise ValueError(
                    "No shipping method found with code '%s'" % code)
        return self.prime_method(basket, method)
