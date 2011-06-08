from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from oscar.apps.address.forms import UserAddressForm
from oscar.views.generic import PostActionMixin

from django.db.models import get_model

order_model = get_model('order', 'Order')
order_line_model = get_model('order', 'Line')
basket_model = get_model('basket', 'Basket')
user_address_model = get_model('address', 'UserAddress')
email_model = get_model('customer', 'email')


class AccountSummaryView(ListView):
    u"""Customer order history"""
    context_object_name = "orders"
    template_name = 'oscar/customer/profile.html'
    paginate_by = 20
    model = order_model

    def get_queryset(self):
        u"""Return a customer's orders"""
        return self.model._default_manager.filter(user=self.request.user)[0:5]

    
class EmailHistoryView(ListView):
    """Customer email history"""
    context_object_name = "emails"
    template_name = 'oscar/customer/email-history.html'
    paginate_by = 20

    def get_queryset(self):
        u"""Return a customer's orders"""
        return email_model._default_manager.filter(user=self.request.user)


class EmailDetailView(DetailView):
    u"""Customer order details"""
    template_name = "oscar/customer/email.html"
    context_object_name = 'email'
    
    def get_object(self):
        u"""Return an order object or 404"""
        return get_object_or_404(email_model, user=self.request.user, id=self.kwargs['email_id'])


class OrderHistoryView(ListView):
    u"""Customer order history"""
    context_object_name = "orders"
    template_name = 'oscar/customer/order-history.html'
    paginate_by = 20
    model = order_model

    def get_queryset(self):
        u"""Return a customer's orders"""
        return self.model._default_manager.filter(user=self.request.user)


class OrderDetailView(DetailView):
    u"""Customer order details"""
    model = order_model
    
    def get_template_names(self):
        return ["oscar/customer/order.html"]    

    def get_object(self):
        return get_object_or_404(self.model, user=self.request.user, number=self.kwargs['order_number'])


class OrderLineView(DetailView, PostActionMixin):
    u"""Customer order line"""
    
    def get_object(self):
        u"""Return an order object or 404"""
        order = get_object_or_404(order_model, user=self.request.user, number=self.kwargs['order_number'])
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


class AddressListView(ListView):
    u"""Customer address book"""
    context_object_name = "addresses"
    template_name = 'oscar/customer/address-book.html'
    paginate_by = 40
        
    def get_queryset(self):
        u"""Return a customer's addresses"""
        return user_address_model._default_manager.filter(user=self.request.user)


class AddressCreateView(CreateView):
    form_class = UserAddressForm
    mode = user_address_model
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.user = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())

    def get_template_names(self):
        return ["oscar/customer/address-create.html"]

    def get_success_url(self):
        return reverse('customer:address-list')


class AddressUpdateView(UpdateView):
    form_class = UserAddressForm
    model = user_address_model
    
    def get_template_names(self):
        return ["oscar/customer/address-form.html"]
    
    def get_success_url(self):
        return reverse('customer:address-detail', kwargs={'pk': self.get_object().pk })


class AddressDeleteView(DeleteView):
    model = user_address_model
    
    def get_success_url(self):
        return reverse('customer:address-list')    
    
    def get_template_names(self):
        return ["oscar/customer/address-delete.html"]
