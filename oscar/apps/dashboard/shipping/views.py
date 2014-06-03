from django.views import generic
from django.core.urlresolvers import reverse
from django.contrib import messages

from oscar.core.loading import get_model


WeightBased = get_model('shipping', 'WeightBased')


class WeightBasedListView(generic.ListView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_list.html"
    context_object_name = "methods"


class WeightBasedCreateView(generic.CreateView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_form.html"

    def get_success_url(self):
        messages.success(self.request, "Shipping method created")
        return reverse('dashboard:shipping-method-list')
