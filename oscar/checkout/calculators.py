



class OrderTotalCalculator(object):
    """
    Calculator class for calculating the order total.
    """
    
    def __init__(self, request):
        # We store a reference to the request as the total may 
        # depend on the user or the other checkout data in the session.
        # Further, it is very likely that it will as shipping method
        # always changes the order total.
        self.request = request
    
    def order_total_incl_tax(self, basket, shipping_method=None):
        # Default to returning the total including tax - use
        # the request.user object if you want to not charge tax
        # to particular customers.  
        total = basket.total_incl_tax
        if shipping_method:
            total += shipping_method.calculate_basket_charge()
        return total
    
    def order_total_excl_tax(self, basket, shipping_method=None):
        total = basket.total_excl_tax
        if shipping_method:
            total += shipping_method.calculate_basket_charge()
        return total