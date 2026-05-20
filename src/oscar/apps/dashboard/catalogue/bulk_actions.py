from django.contrib import messages
from django.db.transaction import atomic
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _, ngettext

from oscar.core.loading import get_classes, get_model
from oscar.views.generic import BulkAction, IntermediateBulkAction

ChildrenBulkActionForm, SetChildrenPriceForm = get_classes(
    "dashboard.catalogue.forms",
    ("ChildrenBulkActionForm", "SetChildrenPriceForm"),
)
Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")


class ProductBulkAction(BulkAction):
    """Base class for a direct bulk action on a list of products."""


class MakePublicAction(ProductBulkAction):
    label = _("Make public")

    @atomic
    def execute(self, request, records):
        for record in records:
            record.is_public = True
            record.save()
        messages.info(
            request,
            ngettext(
                "Public status was successfully updated for %(count)d record.",
                "Public status was successfully updated for %(count)d records.",
                len(records),
            ) % {"count": len(records)},
        )
        return redirect(request.get_full_path())


class MakeNonPublicAction(ProductBulkAction):
    label = _("Make non-public")

    @atomic
    def execute(self, request, records):
        for record in records:
            record.is_public = False
            record.save()
        messages.info(
            request,
            ngettext(
                "Public status was successfully updated for %(count)d record.",
                "Public status was successfully updated for %(count)d records.",
                len(records),
            ) % {"count": len(records)},
        )
        return redirect(request.get_full_path())


class ChildBulkAction(IntermediateBulkAction):
    """Base class for a two-step bulk action that operates on child products."""

    form_class = ChildrenBulkActionForm
    template = "oscar/dashboard/catalogue/product_children_bulk_action.html"

    def execute(self, request, child_ids, form):
        raise NotImplementedError


class MakeChildrenPublicAction(ChildBulkAction):
    label = _("Make children public")

    @atomic
    def execute(self, request, child_ids, form):
        count = Product.objects.filter(
            pk__in=child_ids, structure=Product.CHILD
        ).update(is_public=True)
        messages.info(
            request,
            ngettext(
                "Updated %(count)d child product.",
                "Updated %(count)d child products.",
                count,
            ) % {"count": count},
        )


class MakeChildrenNonPublicAction(ChildBulkAction):
    label = _("Make children non-public")

    @atomic
    def execute(self, request, child_ids, form):
        count = Product.objects.filter(
            pk__in=child_ids, structure=Product.CHILD
        ).update(is_public=False)
        messages.info(
            request,
            ngettext(
                "Updated %(count)d child product.",
                "Updated %(count)d child products.",
                count,
            ) % {"count": count},
        )


class SetChildrenPriceAction(ChildBulkAction):
    label = _("Update children price")
    form_class = SetChildrenPriceForm
    template = "oscar/dashboard/catalogue/product_children_bulk_action_set_price.html"

    @atomic
    def execute(self, request, child_ids, form):
        count = StockRecord.objects.filter(
            product__pk__in=child_ids, product__structure=Product.CHILD
        ).update(price=form.cleaned_data["new_price"])
        messages.info(
            request,
            ngettext(
                "Price updated on %(count)d stockrecord.",
                "Price updated on %(count)d stockrecords.",
                count,
            ) % {"count": count},
        )
