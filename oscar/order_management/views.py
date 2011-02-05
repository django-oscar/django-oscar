from django.http import HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView

from oscar.views import ModelView
from oscar.services import import_module
order_models = import_module('order.models', ['Order', 'BatchLine', 'ShippingEvent', 'ShippingEventType', 'PaymentEvent', 'PaymentEventType'])


class OrderListView(ListView):

    context_object_name = "orders"
    template_name = 'order_management/browse.html'
    paginate_by = 20

    def get_queryset(self):
        return order_models.Order.objects.all()
    
    
class OrderView(ModelView):
    template_file = "order_management/order.html"
    
    def get_model(self):
        return get_object_or_404(order_models.Order, number=self.kwargs['order_number'])
    
    def handle_GET(self, order):
        shipping_options = order_models.ShippingEventType.objects.all()
        payment_options = order_models.PaymentEventType.objects.all()
        
        self.response = render(self.request, self.template_file, locals())
        
    def handle_POST(self, order):
        line_ids = self.request.POST.getlist('order_line')
        lines = order.lines.in_bulk(line_ids)
        
        # Need to determine what kind of event update this is
        if self.request.POST['shipping_event']:
            self.create_shipping_event(order, lines, self.request.POST['shipping_event'])
        elif self.request.POST['payment_event']:
            self.create_payment_event(order, lines, self.request.POST['payment_event'])
        self.response = HttpResponseRedirect(reverse('oscar-order-management-order', kwargs={'order_number': order.number}))
                
    def create_shipping_event(self, order, lines, type_code):
        event_type = order_models.ShippingEventType.objects.get(code=type_code)
        for line in lines.values():
            order_models.ShippingEvent.objects.create(order=order, line=line, 
                                                      quantity=line.quantity, event_type=event_type)
            
    def create_payment_event(self, order, lines, type_code):
        event_type = order_models.PaymentEventType.objects.get(code=type_code)
        for line in lines.values():
            order_models.PaymentEvent.objects.create(order=order, line=line, 
                                                     quantity=line.quantity, event_type=event_type)
    
