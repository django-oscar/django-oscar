from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.generic import ListView

from oscar.core.loading import get_model

ConditionalOffer = get_model("offer", "ConditionalOffer")
Range = get_model("offer", "Range")


class OfferListView(ListView):
    model = ConditionalOffer
    context_object_name = "offers"
    template_name = "oscar/offer/list.html"

    def get_queryset(self):
        """
        Return a queryset of active :py:class:`ConditionalOffer <oscar.apps.offer.abstract_models.AbstractConditionalOffer>`
        instances with an :py:attr:`offer_type <oscar.apps.offer.abstract_models.AbstractConditionalOffer.offer_type>`
        of :py:const:`ConditionalOffer.SITE <oscar.apps.offer.abstract_models.AbstractConditionalOffer.SITE>`.
        """
        return ConditionalOffer.active.filter(offer_type=ConditionalOffer.SITE)


class OfferDetailView(ListView):
    context_object_name = "products"
    template_name = "oscar/offer/detail.html"
    paginate_by = settings.OSCAR_OFFERS_PER_PAGE

    # pylint: disable=W0201
    def get(self, request, *args, **kwargs):
        try:
            self.offer = ConditionalOffer.active.select_related().get(
                slug=self.kwargs["slug"]
            )
        except ConditionalOffer.DoesNotExist:
            raise http.Http404
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["offer"] = self.offer
        ctx["upsell_message"] = self.offer.get_upsell_message(self.request.basket)
        return ctx

    def get_queryset(self):
        """
        Return a queryset of all :py:class:`Product <oscar.apps.catalogue.abstract_models.AbstractProduct>`
        instances related to the :py:class:`ConditionalOffer <oscar.apps.offer.abstract_models.AbstractConditionalOffer>`.
        """
        return self.offer.products()


class RangeDetailView(ListView):
    template_name = "oscar/offer/range.html"
    context_object_name = "products"
    paginate_by = settings.OSCAR_PRODUCTS_PER_PAGE

    # pylint: disable=W0201
    def dispatch(self, request, *args, **kwargs):
        self.range = get_object_or_404(Range, slug=kwargs["slug"], is_public=True)
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return a queryset of all :py:class:`Product <oscar.apps.catalogue.abstract_models.AbstractProduct>`
        instances related to the :py:class:`Range <oscar.apps.offer.abstract_models.AbstractRange>`.
        """
        products = self.range.all_products().browsable()
        return products.order_by("rangeproduct__display_order")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["range"] = self.range
        return ctx
