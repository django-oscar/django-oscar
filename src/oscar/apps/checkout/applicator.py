from oscar.core import prices


class SurchargeList(list):
    @property
    def total(self):
        return sum(self).price


class SurchargeMethod(object):
    method = None
    price = None

    def __init__(self, method, price):
        self.method = method
        self.price = price

    def __add__(self, other):
        price = prices.Price(
            currency=self.price.currency or other.price.currency,
            incl_tax=self.price.incl_tax + other.price.incl_tax,
            excl_tax=self.price.excl_tax + other.price.excl_tax
        )

        return SurchargeMethod(self.method, price)

    def __radd__(self, other):
        if other == 0:
            return self
        else:
            return self.__add__(other)


class SurchargeApplicator(object):

    def __init__(self, request=None, context=None):
        self.context = context
        self.request = request

    def get_surcharges(self, basket, **kwargs):
        """
        For example::
            return (
                PercentageCharge(excl_tax=D("10.0"), incl_tax=D("10.0")),
                FlatCharge(excl_tax=D("20.0"), incl_tax=D("20.0")),
            )

        Surcharges must implement the minimal api in ``oscar.apps.checkout.surcharges.Base``.
        Note that you can also make it a model if you want, just like shipping methods.
        """

        return ()

    def get_applicable_surcharges(self, basket, **kwargs):
        methods = [
            SurchargeMethod(
                method,
                method.calculate(basket)
            )
            for method in self.get_surcharges(basket)
            if self.is_applicable(method, basket)
        ]

        if methods:
            return SurchargeList(methods)
        else:
            return None

    def is_applicable(self, surcharge, basket, **kwargs):
        """
        Checks if surcharge is applicable based on basket and/or shipping address
        """
        return True
