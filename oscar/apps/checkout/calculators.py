# TODO Maybe use a generic price object (similar to partner pricing)
class OrderTotal(object):
    is_tax_known = False

    def __init__(self, excl_tax, incl_tax=None):
        self.excl_tax = excl_tax
        if incl_tax is not None:
            self.incl_tax = incl_tax
            self.is_tax_known = True
            self.tax = incl_tax - excl_tax


class OrderTotalCalculator(object):
    """
    Calculator class for calculating the order total.
    """

    def __init__(self, request=None):
        # We store a reference to the request as the total may
        # depend on the user or the other checkout data in the session.
        # Further, it is very likely that it will as shipping method
        # always changes the order total.
        self.request = request

    def calculate(self, basket, shipping_method, **kwargs):
        excl_tax = basket.total_excl_tax + shipping_method.charge_excl_tax
        if basket.is_tax_known and shipping_method.is_tax_known:
            incl_tax = basket.total_incl_tax + shipping_method.charge_incl_tax
        else:
            incl_tax = None
        return OrderTotal(excl_tax=excl_tax, incl_tax=incl_tax)
