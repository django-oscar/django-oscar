from oscar.checkout.views import ShippingMethodView as OscarShippingMethodView, prev_steps_must_be_complete

    
class ShippingMethodView(OscarShippingMethodView):
    """
    Shipping methods are domain-specific and so need implementing in a 
    subclass of this class.
    """
    
    @prev_steps_must_be_complete
    def __call__(self, request):
        
        assert False
        
        mark_step_as_complete(request)
        return HttpResponseRedirect(reverse(get_next_step(request)))
        
