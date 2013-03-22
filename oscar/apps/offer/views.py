from django.views.generic import ListView
from django.db.models import get_model
from django import http

from oscar.apps.offer.models import ConditionalOffer

Product = get_model('catalogue', 'Product')


class OfferDetailView(ListView):
    context_object_name = 'products'
    template_name = 'offer/detail.html'
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        try:
            self.offer = ConditionalOffer.objects.select_related().get(
                slug=self.kwargs['slug'])
        except ConditionalOffer.DoesNotExist:
            raise http.Http404
        return super(OfferDetailView, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super(OfferDetailView, self).get_context_data(**kwargs)
        ctx['offer'] = self.offer
        ctx['upsell_message'] = self.offer.get_upsell_message(
            self.request.basket)
        return ctx

    def get_queryset(self):
        cond_range = self.offer.condition.range
        if not cond_range:
            return Product.objects.none()
        if cond_range.includes_all_products:
            return Product.browsable.select_related(
                'product_class', 'stockrecord').filter(
                    is_discountable=True).prefetch_related(
                        'variants', 'images', 'product_class__options',
                        'product_options')
        return cond_range.included_products.filter(is_discountable=True)
