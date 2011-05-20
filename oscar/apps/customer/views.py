from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse

from oscar.apps.address.forms import UserAddressForm
from oscar.view.generic import ModelView
from oscar.core.loading import import_module
import_module('address.models', ['UserAddress'], locals())
import_module('order.models', ['Order', 'Line'], locals())
import_module('basket.models', ['Basket'], locals())

@login_required
def profile(request):
    u"""Return a customers's profile"""
    # Load last 5 orders as preview
    orders = Order._default_manager.filter(user=request.user)[0:5]
    return TemplateResponse(request, 'oscar/customer/profile.html', {'orders': orders})
    
        
class OrderHistoryView(ListView):
    u"""Customer order history"""
    context_object_name = "orders"
    template_name = 'oscar/customer/order-history.html'
    paginate_by = 20

    def get_queryset(self):
        u"""Return a customer's orders"""
        return Order._default_manager.filter(user=self.request.user)


class OrderDetailView(ModelView):
    u"""Customer order details"""
    template_file = "oscar/customer/order.html"
    
    def get_model(self):
        u"""Return an order object or 404"""
        return get_object_or_404(Order, user=self.request.user, number=self.kwargs['order_number'])
    
    def handle_GET(self, order):
        self.response = TemplateResponse(self.request, self.template_file, {'order': order})
        
        
class OrderLineView(ModelView):
    u"""Customer order line"""
    
    def get_model(self):
        u"""Return an order object or 404"""
        order = get_object_or_404(Order, user=self.request.user, number=self.kwargs['order_number'])
        return order.lines.get(id=self.kwargs['line_id'])
    
    def handle_GET(self, line):
        return HttpResponseRedirect(reverse('oscar-customer-order-view', kwargs={'order_number': line.order.number}))
    
    def handle_POST(self, line):
        self.response = HttpResponseRedirect(reverse('oscar-customer-order-view', kwargs={'order_number': line.order.number}))
        super(OrderLineView, self).handle_POST(line)
    
    def do_reorder(self, line):
        if not line.product:
            messages.info(self.request, _("This product is no longer available for re-order"))
            return
        
        # We need to pass response to the get_or_create... method
        # as a new basket might need to be created
        self.response = HttpResponseRedirect(reverse('oscar-basket'))
        basket = self.request.basket
        
        # Convert line attributes into basket options
        options = []
        for attribute in line.attributes.all():
            if attribute.option:
                options.append({'option': attribute.option, 'value': attribute.value})
        basket.add_product(line.product, 1, options)
        messages.info(self.request, "Line reordered")
        
        

class AddressBookView(ListView):
    u"""Customer address book"""
    context_object_name = "addresses"
    template_name = 'oscar/customer/address-book.html'
    paginate_by = 40
        
    def get_queryset(self):
        u"""Return a customer's addresses"""
        return UserAddress._default_manager.filter(user=self.request.user)
    
    
class AddressView(ModelView):
    """
    Customer address view
    """
    template_file = "oscar/customer/address-form.html"
    
    def get_model(self):
        """
        Return an address object or a 404
        """
        return get_object_or_404(UserAddress, user=self.request.user, pk=self.kwargs['address_id'])
    
    def handle_GET(self, address):
        form = UserAddressForm(instance=address)
        self.response = TemplateResponse(self.request, self.template_file, {'form': form,
                                                                            'address': address})
        
    def do_save(self, address):
        """
        Save an address
        """
        form = UserAddressForm(self.request.POST, instance=address)
        if form.is_valid():
            form.save()
            self.response = HttpResponseRedirect(reverse('oscar-customer-address-book'))
        else:
            self.response = TemplateResponse(self.request, self.template_file, {'form': form})
            
    def do_delete(self, address):
        """
        Delete an address
        """
        address.delete()
        self.response = HttpResponseRedirect(reverse('oscar-customer-address-book'))
        
    def do_default_billing_address(self, address):
        UserAddress.objects.filter(user=self.request.user).update(default_for_billing=False)
        address.default_for_billing = True
        address.save()
        self.response = HttpResponseRedirect(reverse('oscar-customer-address-book'))
        