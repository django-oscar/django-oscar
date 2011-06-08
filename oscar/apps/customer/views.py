from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse

from oscar.views.generic import PostActionMixin
from oscar.apps.address.forms import UserAddressForm
from oscar.core.loading import import_module
import_module('address.models', ['UserAddress'], locals())
import_module('order.models', ['Order', 'Line'], locals())
import_module('basket.models', ['Basket'], locals())
import_module('customer.models', ['Email'], locals())

@login_required
def profile(request):
    u"""Return a customers's profile"""
    # Load last 5 orders as preview
    orders = Order._default_manager.filter(user=request.user)[0:5]
    emails  = Email._default_manager.filter(user=request.user)[0:5]
    return TemplateResponse(request, 'oscar/customer/profile.html', {'orders': orders,
                                                                     'emails': emails})
    
    
class EmailHistoryView(ListView):
    """Customer email history"""
    context_object_name = "emails"
    template_name = 'oscar/customer/email-history.html'
    paginate_by = 20

    def get_queryset(self):
        u"""Return a customer's orders"""
        return Email._default_manager.filter(user=self.request.user)


class EmailDetailView(DetailView):
    u"""Customer order details"""
    template_name = "oscar/customer/email.html"
    context_object_name = 'email'
    
    def get_object(self):
        u"""Return an order object or 404"""
        return get_object_or_404(Email, user=self.request.user, id=self.kwargs['email_id'])

        
class OrderHistoryView(ListView):
    u"""Customer order history"""
    context_object_name = "orders"
    template_name = 'oscar/customer/order-history.html'
    paginate_by = 20

    def get_queryset(self):
        u"""Return a customer's orders"""
        return Order._default_manager.filter(user=self.request.user)


class OrderDetailView(DetailView):
    u"""Customer order details"""
    template_name = "oscar/customer/order.html"
    context_object_name = 'order'
    
    def get_object(self):
        u"""Return an order object or 404"""
        return get_object_or_404(Order, user=self.request.user, number=self.kwargs['order_number'])
        
        
class OrderLineView(DetailView, PostActionMixin):
    u"""Customer order line"""
    
    def get_object(self):
        u"""Return an order object or 404"""
        order = get_object_or_404(Order, user=self.request.user, number=self.kwargs['order_number'])
        return order.lines.get(id=self.kwargs['line_id'])
    
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
    
    
class AddressView(DetailView, PostActionMixin):
    """
    Customer address view
    """
    template_name = "oscar/customer/address-form.html"
    context_object_name = 'address'
    
    def get_model(self):
        """
        Return an address object or a 404
        """
        return get_object_or_404(UserAddress, user=self.request.user, pk=self.kwargs['address_id'])
    
    def get_context_data(self, **kwargs):
        context = super(AddressView, self).get_context_data(**kwargs)
        context['form'] = UserAddressForm(instance=self.object)
        return context
        
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
        