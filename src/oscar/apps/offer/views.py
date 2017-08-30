from django.views.generic import ListView
from django.shortcuts import get_object_or_404

from oscar.core.loading import get_model
from oscar.apps.offer.models import Range

Product = get_model('catalogue', 'Product')


class RangeDetailView(ListView):
    template_name = 'offer/range.html'
    context_object_name = 'products'

    def dispatch(self, request, *args, **kwargs):
        self.range = get_object_or_404(
            Range, slug=kwargs['slug'], is_public=True)
        return super(RangeDetailView, self).dispatch(
            request, *args, **kwargs)

    def get_queryset(self):
        products = self.range.included_products.all()
        return products.order_by('rangeproduct__display_order')

    def get_context_data(self, **kwargs):
        ctx = super(RangeDetailView, self).get_context_data(**kwargs)
        ctx['range'] = self.range
        return ctx
