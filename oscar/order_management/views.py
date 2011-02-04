from django.http import HttpResponseRedirect
from django.template import Context, loader, RequestContext
from django.shortcuts import render, get_object_or_404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.views.generic import ListView, DetailView

from oscar.services import import_module
order_models = import_module('order.models', ['Order'])


class OrderListView(ListView):

    context_object_name = "orders"
    template_name = 'order_management/browse.html'
    paginate_by = 20

    def get_queryset(self):
        return order_models.Order.objects.all()
    
    
class OrderDetailView(DetailView):
    """
    View a single order.
    """
    context_object_name = "order"
    template_name = "order_management/order.html"
    
    def get_object(self):
        return get_object_or_404(order_models.Order, number=self.kwargs['order_number'])
