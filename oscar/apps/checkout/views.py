from decimal import Decimal
import logging

from django.conf import settings
from django.http import HttpResponse, Http404, HttpResponseRedirect, HttpResponseBadRequest
from django.template import RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.forms import ModelForm
from django.contrib import messages
from django.core.urlresolvers import resolve
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext as _

from oscar.view.generic import ModelView
from oscar.core.loading import import_module

basket_factory = import_module('basket.factory', ['BasketFactory'])
checkout_forms = import_module('checkout.forms', ['ShippingAddressForm'])
checkout_calculators = import_module('checkout.calculators', ['OrderTotalCalculator'])
checkout_utils = import_module('checkout.utils', ['ProgressChecker', 'CheckoutSessionData'])
checkout_signals = import_module('checkout.signals', ['pre_payment', 'post_payment'])
checkout_views = import_module('checkout.core_views', ['CheckoutView', 'mark_step_as_complete'])
order_models = import_module('order.models', ['Order', 'ShippingAddress'])
order_utils = import_module('order.utils', ['OrderNumberGenerator', 'OrderCreator'])
address_models = import_module('address.models', ['UserAddress'])
shipping_repository = import_module('shipping.repository', ['Repository'])


logger = logging.getLogger('oscar.checkout')


class IndexView(object):
    template_file = 'checkout/gateway.html'
    
    def __call__(self, request):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('oscar-checkout-shipping-address'))
        return render(request, self.template_file, locals())    


class ShippingAddressView(checkout_views.CheckoutView):
    template_file = 'checkout/shipping_address.html'
    
    def handle_POST(self):
        if self.request.user.is_authenticated and 'address_id' in self.request.POST:
            address = address_models.UserAddress._default_manager.get(pk=self.request.POST['address_id'])
            if 'action' in self.request.POST and self.request.POST['action'] == 'ship_to':
                # User has selected a previous address to ship to
                self.co_data.ship_to_user_address(address)
                return self.get_success_response()
            elif 'action' in self.request.POST and self.request.POST['action'] == 'delete':
                address.delete()
                messages.info(self.request, "Address deleted from your address book")
                return HttpResponseRedirect(reverse('oscar-checkout-shipping-method'))
            else:
                return HttpResponseBadRequest()
        else:
            form = checkout_forms.ShippingAddressForm(self.request.POST)
            if form.is_valid():
                # Address data is valid - store in session and redirect to next step.
                self.co_data.ship_to_new_address(form.clean())
                return self.get_success_response()
            return self.handle_GET(form)
        
    def handle_GET(self, form=None):
        if not form:
            addr_fields = self.co_data.new_address_fields()
            if addr_fields:
                form = checkout_forms.ShippingAddressForm(addr_fields)
            else:
                form = checkout_forms.ShippingAddressForm()
        self.context['form'] = form
    
        # Look up address book data
        if self.request.user.is_authenticated():
            self.context['addresses'] = address_models.UserAddress._default_manager.filter(user=self.request.user)
        
        return render(self.request, self.template_file, self.context)
    
    
class ShippingMethodView(checkout_views.CheckoutView):
    u"""
    Shipping methods are domain-specific and so need implementing in a 
    subclass of this class.
    """
    template_file = 'checkout/shipping_methods.html';
    
    def handle_GET(self):
        methods = self.get_available_shipping_methods()
        if len(methods) == 1:
            # Only one method - set this and redirect onto the next step
            self.co_data.use_shipping_method(methods[0].code)
            return self.get_success_response()
        
        self.context['methods'] = methods
        return render(self.request, self.template_file, self.context)
    
    def get_shipping_methods_for_basket(self, basket):
        u"""Return available shipping methods for a basket"""
        return shipping_models.Method.objects.all()

    def get_available_shipping_methods(self):
        u"""
        Returns all applicable shipping method objects
        for a given basket.
        """ 
        repo = shipping_repository.Repository()
        return repo.get_shipping_methods(self.request.user, self.basket, self.get_shipping_address())
    
    def handle_POST(self):
        method_code = self.request.POST['method_code']
        self.co_data.use_shipping_method(method_code)
        return self.get_success_response()
        

class PaymentMethodView(checkout_views.CheckoutView):
    u"""
    View for a user to choose which payment method(s) they want to use.
    
    This would include setting allocations if payment is to be split
    between multiple sources.
    """
    pass


class OrderPreviewView(checkout_views.CheckoutView):
    """
    View a preview of the order before submitting.
    """
    
    template_file = 'checkout/preview.html'
    
    def handle_GET(self):
        checkout_views.mark_step_as_complete(self.request)
        return render(self.request, self.template_file, self.context)


class PaymentDetailsView(checkout_views.CheckoutView):
    u"""
    For taking the details of payment and creating the order
    
    The class is deliberately split into fine-grained method, responsible for only one
    thing.  This is to make it easier to subclass and override just one component of
    functionality.
    """

    # Any payment sources should be added to this list as part of the
    # _handle_payment method.  If the order is placed successfully, then
    # they will be persisted.
    payment_sources = []

    def handle_GET(self):
        """
        This method needs to be overridden if there are any payment details
        to be taken from the user, such as a bankcard.
        """
        return self.handle_POST()
    
    def handle_POST(self):
        """
        This method is designed to be overridden by subclasses which will
        validate the forms from the payment details page.  If the forms are valid
        then the method can call submit()."""
        return self.submit()
    
    def submit(self):
        # We generate the order number first as this will be used
        # in payment requests (ie before the order model has been 
        # created).
        order_number = self._generate_order_number(self.basket)
        logger.info(_("Submitting order #%s" % order_number))
        
        # Calculate totals
        calc = checkout_calculators.OrderTotalCalculator(self.request)
        shipping_method = self._get_shipping_method(self.basket)
        total_incl_tax = calc.order_total_incl_tax(self.basket, shipping_method)
        total_excl_tax = calc.order_total_excl_tax(self.basket, shipping_method)
        
        # Handle payment.  Any payment problems should be handled by the 
        # _handle_payment method raise an exception, which should be caught
        # within handle_POST and the appropriate forms redisplayed.
        checkout_signals.pre_payment.send_robust(sender=self, view=self)
        self._handle_payment(order_number, total_incl_tax)
        checkout_signals.post_payment.send_robust(sender=self, view=self)
        
        # Everything is ok, we place the order and save the payment details 
        order = self._place_order(self.basket, order_number, total_incl_tax, total_excl_tax)
        self._save_payment_details(order)
        
        self._reset_checkout()
        
        logger.info(_("Order #%s submitted successfully" % order_number))
        
        # Save order id in session so thank-you page can load it
        self.request.session['checkout_order_id'] = order.id
        return HttpResponseRedirect(reverse('oscar-checkout-thank-you'))
    
    def _generate_order_number(self, basket):
        generator = order_utils.OrderNumberGenerator()
        return generator.order_number(basket)

    def _handle_payment(self, order_number, total):
        """
        Handle any payment processing.  
        
        This method is designed to be overridden within your project.  The
        default is to do nothing.
        """
        pass

    def _save_payment_details(self, order):
        """
        Saves all payment-related details. This could include a billing 
        address, payment sources and any order payment events.
        """
        self._save_payment_events(order)
        self._save_payment_sources(order)

    def _create_billing_address(self):
        """
        Saves any relevant billing data (eg a billing address).
        """
        return None
    
    def _save_payment_events(self, order):
        """
        Saves any relevant payment events for this order
        """
        pass

    def _save_payment_sources(self, order):
        u"""
        Saves any payment sources used in this order.
        
        When the payment sources are created, the order model does not exist and 
        so they need to have it set before saving.
        """
        for source in self.payment_sources:
            source.order = order
            source.save()
    
    def _reset_checkout(self):
        u"""Reset any checkout session state"""
        self.co_data.flush()
        checkout_utils.ProgressChecker().all_steps_complete(self.request)
    
    def _place_order(self, basket, order_number, total_incl_tax, total_excl_tax):
        u"""Writes the order out to the DB"""
        shipping_address = self._create_shipping_address()
        shipping_method = self._get_shipping_method(basket)
        billing_address = self._create_billing_address()
        order_creator = order_utils.OrderCreator()
        return order_creator.place_order(self.request.user, 
                                         basket, 
                                         shipping_address, 
                                         shipping_method, 
                                         billing_address,
                                         total_incl_tax,
                                         total_excl_tax,
                                         order_number)
    
    def _get_shipping_method(self, basket):
        u"""Returns the shipping method object"""
        method = self.co_data.shipping_method()
        method.set_basket(basket)
        return method
    
    def _get_shipping_address(self):
        addr_data = self.co_data.new_address_fields()
        addr_id = self.co_data.user_address_id()
        if addr_data:
            addr = order_models.ShippingAddress(**addr_data)
        elif addr_id:
            addr = address_models.UserAddress._default_manager.get(pk=addr_id)
        return addr
    
    def _create_shipping_address(self):
        u"""Returns the shipping address"""
        addr_data = self.co_data.new_address_fields()
        addr_id = self.co_data.user_address_id()
        if addr_data:
            addr = self._create_shipping_address_from_form_fields(addr_data)
            self._create_user_address(addr_data)
        elif addr_id:
            addr = self._create_shipping_address_from_user_address(addr_id)
        else:
            raise AttributeError("No shipping address data found")
        return addr
    
    def _create_shipping_address_from_form_fields(self, addr_data):
        u"""Creates a shipping address model from the saved form fields"""
        shipping_addr = order_models.ShippingAddress(**addr_data)
        shipping_addr.save() 
        return shipping_addr
    
    def _create_user_address(self, addr_data):
        u"""
        For signed-in users, we create a user address model which will go 
        into their address book.
        """
        if self.request.user.is_authenticated():
            addr_data['user_id'] = self.request.user.id
            user_addr = address_models.UserAddress(**addr_data)
            # Check that this address isn't already in the db as we don't want
            # to fill up the customer address book with duplicate addresses
            try:
                duplicate_addr = address_models.UserAddress._default_manager.get(hash=user_addr.generate_hash())
            except ObjectDoesNotExist:
                user_addr.save()
    
    def _create_shipping_address_from_user_address(self, addr_id):
        u"""Creates a shipping address from a user address"""
        address = address_models.UserAddress._default_manager.get(pk=addr_id)
        # Increment the number of orders to help determine popularity of orders 
        address.num_orders += 1
        address.save()
        
        shipping_addr = order_models.ShippingAddress()
        address.populate_alternative_model(shipping_addr)
        shipping_addr.save()
        return shipping_addr


class ThankYouView(object):
    """
    Displays the 'thank you' page which summarises the order just submitted.
    """
    
    def __call__(self, request):
        try:
            order = order_models.Order._default_manager.get(pk=request.session['checkout_order_id'])
            
            # Remove order number from session to ensure that the thank-you page is only 
            # viewable once.
            del request.session['checkout_order_id']
        except KeyError, ObjectDoesNotExist:
            return HttpResponseRedirect(reverse('oscar-checkout-index'))
        return render(request, 'checkout/thank_you.html', locals())
