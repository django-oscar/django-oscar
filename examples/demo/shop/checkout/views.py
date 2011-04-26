from django.shortcuts import render

from oscar.checkout.views import (ShippingMethodView as CoreShippingMethodView, 
                                  PaymentMethodView as CorePaymentMethodView, 
                                  PaymentDetailsView as CorePaymentDetailsView,
                                  OrderPreviewView as CoreOrderPreviewView,
                                  prev_steps_must_be_complete)
from oscar.payment.forms import BankcardForm, BillingAddressForm
from oscar.services import import_module

shipping_models = import_module('shipping.models', ['Method'])
payment_models = import_module('payment.models', ['Source', 'SourceType'])
    
    
class ShippingMethodView(CoreShippingMethodView):
    
    def get_available_shipping_methods(self):
        codes = ['royal-mail-first-class']
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
        
        
class PaymentDetailsView(CorePaymentDetailsView):
    template_file = 'checkout/payment_details.html'
    
    def handle_GET(self):
        if self._is_cheque_payment():
            self.template_file = 'checkout/payment_details_cheque.html'
        else:
            self.context['bankcard_form'] = BankcardForm()
            self.context['billing_address_form'] = BillingAddressForm()
        return render(self.request, self.template_file, self.context)
    
    def _is_cheque_payment(self):
        payment_method = self.co_data.payment_method()
        return payment_method == 'cheque'

    def handle_POST(self):
        if self._is_cheque_payment():
            return self._submit()

        self.bankcard_form = BankcardForm(self.request.POST)
        self.billing_addr_form = BillingAddressForm(self.request.POST)
        if self.bankcard_form.is_valid() and self.billing_addr_form.is_valid():
            return self._submit()
        self.context['bankcard_form'] = bankcard_form
        self.context['billing_address_form'] = billing_addr_form
        return render(self.request, self.template_file, self.context)

    def _handle_payment(self, basket, order_number):
        if self._is_cheque_payment():
            type = payment_models.SourceType.objects.get(code='cheque')
            allocation = self._get_chargable_total(basket)
            source = payment_models.Source(type=type, allocation=allocation)
            self.payment_sources.append(source)
            return
        self._handle_bankcard_payment()

    def _handle_bankcard_payment(self):
        # Handle payment problems with an exception
        pass

    def _place_order(self, basket, order_number):
        order = super(PaymentDetailsView, self)._place_order(basket, order_number)
        if self._is_cheque_payment():
            # Set order status as on hold
            pass
        return order
