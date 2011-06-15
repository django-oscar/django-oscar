import operator
from urllib import urlencode

from django.http import HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.template.response import TemplateResponse
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView

from django.template.response import TemplateResponse
from django.contrib import messages
from django.db import transaction
from django.db.models import Q
from django.contrib.comments.views.moderation import delete

from oscar.core.loading import import_module
from oscar.views.generic import PostActionMixin
import_module('order.models', ['Order', 'Line', 'ShippingEvent', 'ShippingEventQuantity', 
                               'ShippingEventType', 'PaymentEvent', 'PaymentEventType', 'OrderNote'], locals())
import_module('order_management.forms', ['SimpleSearch'], locals())


class OrderListView(ListView):
    u"""A list of orders"""
    context_object_name = "orders"
    template_name = 'order_management/browse.html'
    paginate_by = 20

    def get_queryset(self):
        if 'search_query' in self.request.GET and self.request.GET['search_query'].strip():
            q = self.request.GET['search_query'].strip()
            q_list = [Q(number__icontains=q)]
            search_by = self.request.GET.getlist('search_by')
            if search_by:
                if 'billing_address' in search_by:
                    q_list.append(Q(billing_address__search_text__icontains=q))
                if 'shipping_address' in search_by:
                    q_list.append(Q(shipping_address__search_text__icontains=q))
                if 'customer' in search_by:
                    q_list.append(Q(number__icontains=q))
                    q_list.append(Q(user__first_name__icontains=q))
                    q_list.append(Q(user__last_name__icontains=q))
                    q_list.append(Q(user__email__icontains=q))
            return Order._default_manager.filter(reduce(operator.or_, q_list))
        return Order._default_manager.all()
    
    def get_context_data(self, **kwargs):
        context = super(OrderListView, self).get_context_data(**kwargs)
        search_params = self.request.GET.copy()
        if 'page' in search_params:
            del(search_params['page'])
        context['search_params'] = '&' + search_params.urlencode()
        context['order_simple_search_form'] = SimpleSearch(self.request.GET)
        return context
    
    def get(self, request, *args, **kwargs):
        response = super(OrderListView, self).get(request, *args, **kwargs)
        return response
        
        
class OrderDetailView(DetailView, PostActionMixin):
    u"""A detail view of an order"""
    template_name = "order_management/order.html"
    context_object_name = 'order'
    
    def get_object(self):
        u"""Return an order object or a 404"""
        return get_object_or_404(Order, number=self.kwargs['order_number'])
    
    def get_context_data(self, **kwargs):
        context = super(OrderDetailView, self).get_context_data(**kwargs)
        context['shipping_options'] = ShippingEventType._default_manager.all()
        context['payment_options'] = PaymentEventType._default_manager.all()
        return context
      
    def post(self, request, *args, **kwargs):
        order = self.get_object()
        self.response = HttpResponseRedirect(reverse('oscar-order-management-order', kwargs={'order_number': order.number}))
        return super(OrderDetailView, self).post(request, *args, **kwargs)
   
    def do_create_order_event(self, order):
        self.create_shipping_event(order, order.lines.all())
        
    def do_create_line_event(self, order):
        u"""Create an event for an order"""
        line_ids = self.request.POST.getlist('order_line')
        lines = order.lines.in_bulk(line_ids)
        if not len(lines):
            messages.info(self.request, "Please select some lines")
            return
        try:
            if self.request.POST['shipping_event']:
                self.create_shipping_event(order, lines.values())
        except (AttributeError, ValueError), e:
            messages.error(self.request, str(e))    
                
    def create_shipping_event(self, order, lines):
        u"""Create a shipping event for an order"""
        with transaction.commit_on_success():
            event_type = ShippingEventType._default_manager.get(code=self.request.POST['shipping_event'])
            event = ShippingEvent._default_manager.create(order=order, event_type=event_type)
            for line in lines:
                try:
                    event_quantity = int(self.request.POST['order_line_quantity_%d' % line.id])
                except KeyError:
                    event_quantity = line.quantity
                ShippingEventQuantity._default_manager.create(event=event, line=line, 
                                                                  quantity=event_quantity)
            
    def create_payment_event(self, order, lines, type_code):
        u"""Create a payment event for an order"""
        event_type = PaymentEventType._default_manager.get(code=type_code)
        for line in lines.values():
            order_models.PaymentEvent._default_manager.create(order=order, line=line, 
                                                     quantity=line.quantity, event_type=event_type)
            
    def do_add_note(self, order):
        u"""Save a note against an order."""
        if self.request.user.is_authenticated():
            message = self.request.POST['message'].strip()
            if message:
                messages.info(self.request, "Message added")
                OrderNote._default_manager.create(order=order, message=self.request.POST['message'],
                                                         user=self.request.user)
            else:
                messages.info(self.request, "Please enter a message")
    
