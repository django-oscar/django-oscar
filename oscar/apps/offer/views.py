from django.views.generic import ListView
from django.db.models import get_model, F, Q
from django import http
from django.shortcuts import get_object_or_404

from oscar.apps.offer.models import ConditionalOffer, Range

Product = get_model('catalogue', 'Product')

public_offer_q = (
    Q(num_applications__lt=F('max_global_applications')) | \
    Q(max_global_applications__isnull=True)) & \
    Q(status=ConditionalOffer.OPEN) & \
    Q(offer_type=ConditionalOffer.SITE)


class OfferListView(ListView):
    model = ConditionalOffer
    context_object_name = 'offers'
    template_name = 'offer/list.html'

    def get_queryset(self):
        return ConditionalOffer.active.filter(public_offer_q)


class OfferDetailView(ListView):
    context_object_name = 'products'
    template_name = 'offer/detail.html'
    paginate_by = 20

    def get(self, request, *args, **kwargs):
        self.offer = get_object_or_404(
            ConditionalOffer.active.filter(public_offer_q).select_related(),
            slug=self.kwargs['slug'])
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
        return self.range.included_products.all()

    def get_context_data(self, **kwargs):
        ctx = super(RangeDetailView, self).get_context_data(**kwargs)
        ctx['range'] = self.range
        return ctx
