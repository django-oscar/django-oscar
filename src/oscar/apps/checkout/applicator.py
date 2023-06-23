class SurchargeList(list):
    @property
    def total(self):
        return sum([surcharge.price for surcharge in self])


class SurchargePrice:
    surcharge = None
    price = None

    def __init__(self, surcharge, price):
        self.surcharge = surcharge
        self.price = price


class SurchargeApplicator:
    def __init__(self, request=None, context=None):
        self.context = context
        self.request = request

    # pylint: disable=unused-argument
    def get_surcharges(self, basket, **kwargs):
        """
        For example::
            return (
                PercentageCharge(percentage=D("2.00")),
                FlatCharge(excl_tax=D("20.0"), incl_tax=D("20.0")),
            )

        Surcharges must implement the minimal API in ``oscar.apps.checkout.surcharges.BaseSurcharge``.
        Note that you can also make it a model if you want, just like shipping methods.
        """

        return ()

    def get_applicable_surcharges(self, basket, **kwargs):
        methods = [
            SurchargePrice(surcharge, surcharge.calculate(basket=basket, **kwargs))
            for surcharge in self.get_surcharges(basket=basket, **kwargs)
            if self.is_applicable(surcharge=surcharge, basket=basket, **kwargs)
        ]

        if methods:
            return SurchargeList(methods)
        else:
            return None

    # pylint: disable=unused-argument
    def is_applicable(self, surcharge, basket, **kwargs):
        """
        Checks if surcharge is applicable to certain conditions
        """
        return True
