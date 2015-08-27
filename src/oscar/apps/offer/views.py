from django.views.generic import ListView
from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404

from oscar.core.loading import get_model

ConditionalOffer = get_model('offer', 'ConditionalOffer')
Range = get_model('offer', 'Range')
Product = get_model('catalogue', 'Product')


class OfferListView(ListView):
    model = ConditionalOffer
    context_object_name = 'offers'
    template_name = 'offer/list.html'

    def get_queryset(self):
        return ConditionalOffer.active.filter(
            offer_type=ConditionalOffer.SITE)


class OfferDetailView(ListView):
    context_object_name = 'products'
    template_name = 'offer/detail.html'
    paginate_by = settings.OSCAR_OFFERS_PER_PAGE

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
        return self.offer.products()


class RangeDetailView(ListView):
    template_name = 'offer/range.html'
    context_object_name = 'products'

    def dispatch(self, request, *args, **kwargs):
        self.range = get_object_or_404(
            Range, slug=kwargs['slug'], is_public=True)
        return super(RangeDetailView, self).dispatch(
            request, *args, **kwargs)

    def get_queryset(self):
        products = self.range.all_products()
        return products.order_by('rangeproduct__display_order')

    def get_context_data(self, **kwargs):
        ctx = super(RangeDetailView, self).get_context_data(**kwargs)
        ctx['range'] = self.range
        return ctx
