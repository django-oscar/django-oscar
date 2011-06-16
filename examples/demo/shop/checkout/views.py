from django.template.response import TemplateResponse

from oscar.apps.checkout.views import (PaymentMethodView as CorePaymentMethodView, 
                                  PaymentDetailsView as CorePaymentDetailsView,
                                  OrderPreviewView as CoreOrderPreviewView)
from oscar.apps.payment.forms import BankcardForm, BillingAddressForm
from oscar.apps.shipping.methods import ShippingMethod
from oscar.core.loading import import_module
import_module('payment.models', ['Source', 'SourceType'], locals())
import_module('payment.exceptions', ['TransactionDeclinedException'], locals())
import_module('payment.utils', ['Bankcard'], locals())    
import_module('payment.datacash.utils', ['Gateway', 'Facade'], locals())
import_module('order.models', ['PaymentEvent', 'PaymentEventType', 'PaymentEventQuantity'], locals())
    
    
class PaymentMethodView(CorePaymentMethodView):
    template_file = 'checkout/payment_method.html'
    
    def handle_GET(self):
        return TemplateResponse(self.request, self.template_file, self.context)
    
    def handle_POST(self):
        method = self.request.POST['method_code']
        self.co_data.pay_by(method)
        return self.get_success_response()
    
    
class OrderPreviewView(CoreOrderPreviewView):
    u"""View a preview of the order before submitting."""
    
    def handle_GET(self):
        # Forward straight onto the payment details - no need for preview
        return self.get_success_response()   
        
        
class PaymentDetailsView(CorePaymentDetailsView):
    template_file = 'checkout/payment_details.html'
    
    def handle_GET(self):
        if self.is_cheque_payment():
            self.template_file = 'checkout/payment_details_cheque.html'
        else:
            shipping_addr = self.get_shipping_address()
            card_values = {'name': shipping_addr.name()}
            self.context['bankcard_form'] = BankcardForm(initial=card_values)
            addr_values = {'first_name': shipping_addr.first_name,
                           'last_name': shipping_addr.last_name,}
            self.context['billing_address_form'] = BillingAddressForm(initial=addr_values)
        return TemplateResponse(self.request, self.template_file, self.context)
    
    def handle_POST(self):
        if self.is_cheque_payment():
            return self.submit()
        try:    
            self.bankcard_form = BankcardForm(self.request.POST)
            self.billing_addr_form = BillingAddressForm(self.request.POST)
            if self.bankcard_form.is_valid() and self.billing_addr_form.is_valid():
                return self.submit()
        except TransactionDeclinedException, e:
            self.context['payment_error'] = str(e)
        
        self.context['bankcard_form'] = self.bankcard_form
        self.context['billing_address_form'] = self.billing_addr_form
        return TemplateResponse(self.request, self.template_file, self.context)

    def handle_payment(self, order_number, total):
        if self.is_cheque_payment():
            self.handle_cheque_payment(total)
        else:    
            self.handle_bankcard_payment(order_number, total)

    def is_cheque_payment(self):
        payment_method = self.co_data.payment_method()
        return payment_method == 'cheque'

    def handle_cheque_payment(self, total):
        # Nothing to do except create a payment source
        type,_ = SourceType.objects.get_or_create(name="Cheque")
        source = Source(type=type, allocation=total)
        self.payment_sources.append(source)

    def handle_bankcard_payment(self, order_number, total):
        # Handle payment problems with an exception
        # Make payment submission - handle response from DC
        # - could be an iframe open
        # - could be failure
        # - could be redirect
        
        # Create bankcard object
        bankcard = self.bankcard_form.get_bankcard_obj()
        
        # Handle new card submission 
        dc_facade = Facade()
        reference = dc_facade.debit(order_number, total, bankcard, self.basket)
        
        # Create payment source (but don't save just yet)
        type,_ = SourceType.objects.get_or_create(name='DataCash', code='datacash')
        source = Source(type=type,
               allocation=total,
               amount_debited=total,
               reference=reference)
        self.payment_sources.append(source)

    def place_order(self, basket, order_number, total_incl_tax, total_excl_tax):
        order = super(PaymentDetailsView, self).place_order(basket, order_number, total_incl_tax, total_excl_tax)
        if self.is_cheque_payment():
            order.status = "Awaiting cheque"
            order.save()
        return order
    
    def create_billing_address(self):
        if not hasattr(self, 'billing_addr_form'):
            return None
        return self.billing_addr_form.save()
        
    def save_payment_events(self, order):
        event_type,_ = PaymentEventType.objects.get_or_create(code="paid-for")
        event = PaymentEvent.objects.create(order=order, event_type=event_type)
        for line in order.lines.all():
            line_qty = PaymentEventQuantity.objects.create(event=event, 
                                                           line=line,
                                                           quantity=line.quantity)
