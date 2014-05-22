from decimal import Decimal as D

from oscar.apps.shipping import repository, methods


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
