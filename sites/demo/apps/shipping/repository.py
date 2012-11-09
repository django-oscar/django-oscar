from decimal import Decimal as D
from oscar.apps.shipping.methods import FixedPrice, NoShippingRequired
from oscar.apps.shipping.repository import Repository as CoreRepository

# Dummy shipping methods
method1 = FixedPrice(D('12.00'))
method1.code = 'method1'
method1.name = 'Ship by van'

method2 = FixedPrice(D('24.00'))
method2.code = 'method2'
method2.name = 'Ship by pigeon'
method2.description = 'Here is a description of this shipping method'


class Repository(CoreRepository):
    methods = {
        method1.code: method1,
        method2.code: method2,
    }

    def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
        methods = self.methods.values()
        return self.prime_methods(basket, methods)

    def find_by_code(self, code, basket):
        if code == NoShippingRequired.code:
            method = NoShippingRequired()
        else:
            method = self.methods.get(code, None)
        return self.prime_method(basket, method)
