from django.shortcuts import render

from oscar.checkout.views import (ShippingMethodView as CoreShippingMethodView, 
                                  PaymentView as CorePaymentView, prev_steps_must_be_complete)
from oscar.payment.forms import BankcardForm
from oscar.services import import_module

shipping_models = import_module('shipping.models', ['Method'])

    
class ShippingMethodView(CoreShippingMethodView):
    
    def get_shipping_methods_for_basket(self, basket):
        codes = ['royal-mail-first-class']
        # Only allow parcel force if dropship products are include
        for line in basket.lines.all():
            if line.product.stockrecord.partner_id == 2:
                codes.append('parcel-force')
        return shipping_models.Method.objects.filter(code__in=codes)

    
class PaymentView(CorePaymentView):
    
    @prev_steps_must_be_complete
    def __call__(self, request):
        
        assert False
        
        # Display credit card form
        form = BankcardForm()
        
        return render(request, 'checkout/payment.html', locals())
        
    def success(self):
        
        mark_step_as_complete(request)
        return HttpResponseRedirect(reverse(get_next_step(request)))
        

