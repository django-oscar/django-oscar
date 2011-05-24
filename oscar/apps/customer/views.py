from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext as _
from django.template.response import TemplateResponse

from oscar.apps.address.forms import UserAddressForm
from oscar.view.generic import ModelView

from django.db.models import get_model

order_model = get_model('order', 'Order')
order_line_model = get_model('order', 'Line')
basket_model = get_model('basket', 'Basket')
user_address_model = get_model('address', 'UserAddress')


class AccountSummaryView(ListView):
    u"""Customer order history"""
    context_object_name = "orders"
    template_name = 'oscar/customer/profile.html'
    paginate_by = 20
    model = order_model

    def get_queryset(self):
        u"""Return a customer's orders"""
        return self.model._default_manager.filter(user=self.request.user)[0:5]


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
    
    def get_queryset(self):
        return self.model._default_manager.filter(user=self.request.user)
    
    def get_object(self):
        try:
            return self.get_queryset().get(number=self.kwargs['order_number'])
        except self.model.DoesNotExist:
            raise Http404()

        
class OrderLineView(ModelView):
    u"""Customer order line"""
    
    def get_model(self):
        u"""Return an order object or 404"""
        order = get_object_or_404(order_model, user=self.request.user, number=self.kwargs['order_number'])
        return order.lines.get(id=self.kwargs['line_id'])
    
    def handle_GET(self, line):
        return HttpResponseRedirect(reverse('customer:order', kwargs={'order_number': line.order.number}))
    
    def handle_POST(self, line):
        self.response = HttpResponseRedirect(reverse('customer:order', kwargs={'order_number': line.order.number}))
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
