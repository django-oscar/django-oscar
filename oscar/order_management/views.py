from django.http import HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView

from oscar.views import ModelView
from oscar.services import import_module
order_models = import_module('order.models', ['Order', 'BatchLine', 'ShippingEvent', 'ShippingEventType', 'PaymentEventType'])


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
        
        self.response = HttpResponseRedirect(reverse('oscar-order-management-order', kwargs={'order_number': order.number}))
        
        line_ids = self.request.POST.getlist('order_line')
        
        # Need to determine what kind of event update this is
        if self.request.POST['shipping_event']:
            # Load event type obj
            event_type = order_models.ShippingEventType.objects.get(code=self.request.POST['shipping_event'])
            
            # Need to load lines in a way that checks they are from the order 
            lines = order_models.BatchLine.objects.in_bulk(line_ids)
            for line in lines.values():
                order_models.ShippingEvent.objects.create(order=order, line=line, quantity=line.quantity, event_type=event_type)
        
        
    
