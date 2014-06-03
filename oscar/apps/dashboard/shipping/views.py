from django.views import generic

from oscar.core.loading import get_model


WeightBased = get_model('shipping', 'WeightBased')


class WeightBasedListView(generic.ListView):
    model = WeightBased
    template_name = "dashboard/shipping/weight_based_list.html"
    context_object_name = "methods"
