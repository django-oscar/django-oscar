from django.contrib import messages
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _, ngettext

from oscar.core.loading import get_classes, get_model
from oscar.views.generic import BulkAction, IntermediateBulkAction

ChildrenBulkActionForm, SetChildrenPriceForm = get_classes(
    "dashboard.catalogue.forms",
    ("ChildrenBulkActionForm", "SetChildrenPriceForm"),
)
Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")


class MakePublicAction(BulkAction):
    label = _("Make public")

    @atomic
    def execute(self, request, records):
        count = Product.objects.filter(pk__in=[r.pk for r in records]).update(
            is_public=True
        )
        messages.success(
            request,
            ngettext(
                "Public status was successfully updated for %(count)d record.",
                "Public status was successfully updated for %(count)d records.",
                count,
            )
            % {"count": count},
        )


class MakeNonPublicAction(BulkAction):
    label = _("Make non-public")

    @atomic
    def execute(self, request, records):
        count = Product.objects.filter(pk__in=[r.pk for r in records]).update(
            is_public=False
        )
        messages.success(
            request,
            ngettext(
                "Public status was successfully updated for %(count)d record.",
                "Public status was successfully updated for %(count)d records.",
                count,
            )
            % {"count": count},
        )


class ChildBulkAction(IntermediateBulkAction):
    """Base class for a two-step bulk action that operates on child products."""

    form_class = ChildrenBulkActionForm
    template = "oscar/dashboard/catalogue/product_children_bulk_action.html"

    def execute(self, request, child_ids, form):
        raise NotImplementedError


class MakeChildrenPublicAction(ChildBulkAction):
    label = _("Make variants public")

    @atomic
    def execute(self, request, child_ids, form):
        count = Product.objects.filter(
            pk__in=child_ids, structure=Product.CHILD
        ).update(is_public=True)
        messages.success(
            request,
            ngettext(
                "Updated %(count)d variant.",
                "Updated %(count)d variants.",
                count,
            )
            % {"count": count},
        )


class MakeChildrenNonPublicAction(ChildBulkAction):
    label = _("Make variants non-public")

    @atomic
    def execute(self, request, child_ids, form):
        count = Product.objects.filter(
            pk__in=child_ids, structure=Product.CHILD
        ).update(is_public=False)
        messages.success(
            request,
            ngettext(
                "Updated %(count)d variant.",
                "Updated %(count)d variants.",
                count,
            )
            % {"count": count},
        )


class SetChildrenPriceAction(ChildBulkAction):
    label = _("Update variant prices")
    form_class = SetChildrenPriceForm
    template = "oscar/dashboard/catalogue/product_children_bulk_action_set_price.html"

    @atomic
    def execute(self, request, child_ids, form):
        count = StockRecord.objects.filter(
            product__pk__in=child_ids, product__structure=Product.CHILD
        ).update(price=form.cleaned_data["new_price"])
        messages.success(
            request,
            ngettext(
                "Price updated on %(count)d stockrecord.",
                "Price updated on %(count)d stockrecords.",
                count,
            )
            % {"count": count},
        )
