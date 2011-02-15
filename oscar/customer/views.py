from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from oscar.address.forms import UserAddressForm
from oscar.views import ModelView
from oscar.services import import_module
address_models = import_module('address.models', ['UserAddress'])
order_models = import_module('order.models', ['Order'])

@login_required
def profile(request):
    # Load last 5 orders as preview
    orders = order_models.Order.objects.filter(user=request.user)[0:5]
    return render(request, 'customer/profile.html', locals())
    
        
class OrderHistoryView(ListView):
    context_object_name = "orders"
    template_name = 'customer/order-history.html'
    paginate_by = 20

    def get_queryset(self):
        return order_models.Order.objects.filter(user=self.request.user)


class OrderDetailView(ModelView):
    template_file = "customer/order.html"
    
    def get_model(self):
        return get_object_or_404(order_models.Order, user=self.request.user, number=self.kwargs['order_number'])
    
    def handle_GET(self, order):
        self.response = render(self.request, self.template_file, locals())
        

class AddressBookView(ListView):
    context_object_name = "addresses"
    template_name = 'customer/address-book.html'
    paginate_by = 40
        
    def get_queryset(self):
        return address_models.UserAddress.objects.filter(user=self.request.user)
    
    
class AddressView(ModelView):
    template_file = "customer/address-form.html"
    
    def get_model(self):
        return get_object_or_404(address_models.UserAddress, user=self.request.user, pk=self.kwargs['address_id'])
    
    def handle_GET(self, address):
        form = UserAddressForm(instance=address)
        self.response = render(self.request, self.template_file, locals())
        
    def do_save(self, address):
        form = UserAddressForm(self.request.POST, instance=address)
        if form.is_valid():
            a = form.save()
            self.response = HttpResponseRedirect(reverse('oscar-customer-address-book'))
        else:
            self.response = render(self.request, self.template_file, locals())
            
    def do_delete(self, address):
        address.delete()
        self.response = HttpResponseRedirect(reverse('oscar-customer-address-book'))
            