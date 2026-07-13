from django.db.models import Q
from django.urls import reverse

from oscar.core.loading import get_classes
from oscar.views.generic import BulkEditMixin, IntermediateBulkEditMixin

(
    MakePublicAction,
    MakeNonPublicAction,
    MakeProductsPublicAction,
    MakeProductsNonPublicAction,
    SetProductPriceAction,
) = get_classes(
    "dashboard.catalogue.bulk_actions",
    (
        "MakePublicAction",
        "MakeNonPublicAction",
        "MakeProductsPublicAction",
        "MakeProductsNonPublicAction",
        "SetProductPriceAction",
    ),
)


class PartnerProductFilterMixin:
    def filter_queryset(self, queryset):
        """
        Restrict the queryset to products the given user has access to.
        A staff user is allowed to access all Products.
        A non-staff user is only allowed access to a product if they are in at
        least one stock record's partner user list.
        """
        user = self.request.user
        if user.is_staff:
            return queryset

        return queryset.filter(
            Q(children__stockrecords__partner__users__pk=user.pk)
            | Q(stockrecords__partner__users__pk=user.pk)
        ).distinct()


class ProductBulkActionMixin(IntermediateBulkEditMixin):
    """Mixin that implements bulk actions for the product list view."""

    actions = {}
    intermediate_actions = {
        "make_products_public": MakeProductsPublicAction(),
        "make_products_non_public": MakeProductsNonPublicAction(),
        "set_product_price": SetProductPriceAction(),
    }

    def get_actions(self):
        return {**super().get_actions(), **self.intermediate_actions}

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = self.get_actions()
        return ctx

    def get_intermediate_url(self, request, action):
        return reverse("dashboard:catalogue-product-bulk-action")


class CategoryBulkActionMixin(BulkEditMixin):
    """Mixin that implements bulk actions for category list views."""

    actions = {
        "make_public": MakePublicAction(),
        "make_non_public": MakeNonPublicAction(),
    }

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = self.actions
        return ctx
