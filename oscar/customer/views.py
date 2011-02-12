from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView

from oscar.views import ModelView
from oscar.services import import_module
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