from oscar.checkout.views import (ShippingMethodView as CoreShippingMethodView, 
                                  PaymentView as CorePaymentView, prev_steps_must_be_complete)
from oscar.services import import_module

shipping_models = import_module('shipping.models', ['Method'])
    
class ShippingMethodView(CoreShippingMethodView):
    
    def get_shipping_methods_for_basket(self, basket):
        codes = ['royal-mail-first-class']
        # Only allow parcel force if dropship products are include
        for line in basket.lines.all():
            if line.product.stockrecord.partner_id == 1:
                codes.append('parcel-force')
        return shipping_models.Method.objects.filter(code__in=codes)

    
class PaymentView(CorePaymentView):
    pass
        
