from django.http import HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.db import transaction
from django.template.response import TemplateResponse

from oscar.view.generic import ModelView
from oscar.core.loading import import_module
import_module('order.models', ['Order', 'Line', 'ShippingEvent', 'ShippingEventQuantity', 
                               'ShippingEventType', 'PaymentEvent', 'PaymentEventType', 'OrderNote'], locals())


class OrderListView(ListView):
    u"""A list of orders"""
    context_object_name = "orders"
    template_name = 'oscar/order_management/browse.html'
    paginate_by = 20

    def get_queryset(self):
        return Order._default_manager.all()
    
  
class OrderView(ModelView):
    u"""A detail view of an order"""
    template_file = "oscar/order_management/order.html"
    
    def get_model(self):
        u"""Return an order object or a 404"""
        return get_object_or_404(Order, number=self.kwargs['order_number'])
    
    def handle_GET(self, order):
        shipping_options = ShippingEventType._default_manager.all()
        payment_options = PaymentEventType._default_manager.all()
        self.response = TemplateResponse(self.request, self.template_file, {'order': order,
                                                                            'shipping_options': shipping_options,
                                                                            'payment_options': payment_options})
        
    def handle_POST(self, order):
        self.response = HttpResponseRedirect(reverse('oscar-order-management-order', kwargs={'order_number': order.number}))
        super(OrderView, self).handle_POST(order)
    
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
    
