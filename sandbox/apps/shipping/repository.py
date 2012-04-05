from oscar.apps.shipping.methods import Free
from oscar.apps.shipping.repository import Repository as CoreRepository


class Repository(CoreRepository):

    def get_shipping_methods(self, user, basket, shipping_addr=None, **kwargs):
        methods = [Free(), Free()]
        return self.add_basket_to_methods(basket, methods)
