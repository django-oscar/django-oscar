from django.views.generic import ListView
from django.db.models import get_model
from django import http

from oscar.apps.offer.models import ConditionalOffer

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
        return self.offer.products()
