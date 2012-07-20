from oscar.apps.shipping.methods import Free, NoShippingRequired
from oscar.apps.shipping.repository import Repository as CoreRepository

# Dummy shipping methods
free1 = Free()
free1.code = 'free1'
free1.description = 'Ship by van'

free2 = Free()
free2.code = 'free2'
free2.description = 'Ship by boat'


class Repository(CoreRepository):

    methods = {
        free1.code: free1,
        free2.code: free2
    }

    def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
        methods = self.methods.values()
        return self.add_basket_to_methods(basket, methods)

    def find_by_code(self, code):
        if code == NoShippingRequired.code:
            return NoShippingRequired()
        return self.methods.get(code, None)
