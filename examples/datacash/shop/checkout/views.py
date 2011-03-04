from django.shortcuts import render

from oscar.checkout.views import (ShippingMethodView as CoreShippingMethodView, 
                                  PaymentMethodView as CorePaymentMethodView, 
                                  PaymentDetailsView as CorePaymentDetailsView,
                                  OrderPreviewView as CoreOrderPreviewView,
                                  SubmitView as CoreSubmitView,
                                  prev_steps_must_be_complete)
from oscar.payment.forms import BankcardForm, BillingAddressForm
from oscar.services import import_module

shipping_models = import_module('shipping.models', ['Method'])
    
class ShippingMethodView(CoreShippingMethodView):
    
    def get_available_shipping_methods(self):
        codes = ['royal-mail-first-class']
        # Only allow parcel force if dropship products are include
        for line in self.basket.lines.all():
            if line.product.stockrecord.partner_id == 2:
                codes.append('parcel-force')
        return shipping_models.Method.objects.filter(code__in=codes)

    
class PaymentMethodView(CorePaymentMethodView):
    template_file = 'checkout/payment_method.html'
    
    def handle_GET(self):
        return render(self.request, self.template_file, self.context)
    
    def handle_POST(self):
        method = self.request.POST['method_code']
        self.co_data.pay_by(method)
        return self.get_success_response()
    
    
class OrderPreviewView(CoreOrderPreviewView):
    u"""View a preview of the order before submitting."""
    
    def handle_GET(self):
        # Forward straight onto the payment details
        return self.get_success_response()   
        
        
class PaymentDetailsView(CorePaymentMethodView):
    template_file = 'checkout/payment_details.html'
    
    def handle_GET(self):
        
        # Need a billing address form and a bankcard form
        self.context['bankcard_form'] = BankcardForm()
        self.context['billing_address_form'] = BillingAddressForm()
        
        return render(self.request, self.template_file, self.context)
    
    def handle_POST(self):
        assert False
        

class SubmitView(CoreSubmitView):
    
    def _handle_payment(self, basket):
        u"""Handle any payment processing"""
        
        bankcard_form = BankcardForm(request.POST)
        if not bankcard_form.is_valid():
            # Put form into the session and redirect back 
            self.request.session['bankcard_form'] = bankcard_form
            
        assert False
