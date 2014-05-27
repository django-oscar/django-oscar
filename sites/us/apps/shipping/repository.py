from decimal import Decimal as D

from oscar.apps.shipping import repository, methods, models


class Standard(methods.FixedPrice):
    def __init__(self):
        super(Standard, self).__init__(
            charge_excl_tax=D('10.00'))


class Express(methods.FixedPrice):
    def __init__(self):
        super(Express, self).__init__(
            charge_excl_tax=D('20.00'))


class Repository(repository.Repository):
    methods = [Standard, Express]

    def get_shipping_methods(self, user, basket, shipping_addr=None,
                             request=None, **kwargs):
        methods = super(Repository, self).get_shipping_methods(
            user, basket, shipping_addr, request, **kwargs)

        item_methods = models.OrderAndItemCharges.objects.filter(
            countries=shipping_addr.country)
        for method in item_methods:
            methods.append(self.prime_method(basket, method))

        return methods
