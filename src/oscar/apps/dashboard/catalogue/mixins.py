from django.db.models import Q
from django.urls import reverse

from oscar.core.loading import get_classes
from oscar.views.generic import IntermediateBulkEditMixin

(
    MakePublicAction,
    MakeNonPublicAction,
    MakeChildrenPublicAction,
    MakeChildrenNonPublicAction,
    SetChildrenPriceAction,
) = get_classes(
    "dashboard.catalogue.bulk_actions",
    (
        "MakePublicAction",
        "MakeNonPublicAction",
        "MakeChildrenPublicAction",
        "MakeChildrenNonPublicAction",
        "SetChildrenPriceAction",
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


class CatalogueBulkActionMixin(IntermediateBulkEditMixin):
    # Dict of action name → label. Used both as the dispatch whitelist (dict
    # keys) and as the data source for the bulk-actions dropdown in the template.
    # Subclasses can extend this dict to add further actions.
    actions = {
        "make_public": MakePublicAction(),
        "make_non_public": MakeNonPublicAction(),
        "make_children_public": MakeChildrenPublicAction(),
        "make_children_non_public": MakeChildrenNonPublicAction(),
        "set_children_price": SetChildrenPriceAction(),
    }
    intermediate_actions = (
        "make_children_public",
        "make_children_non_public",
        "set_children_price",
    )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["actions"] = self.get_actions()
        return ctx

    def get_intermediate_url(self, request, action):
        return reverse("dashboard:catalogue-product-children-bulk-action")

