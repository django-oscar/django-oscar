from django.contrib import messages
from django.db.transaction import atomic
from django.utils.translation import gettext_lazy as _, ngettext

from oscar.core.loading import get_classes, get_model

ChildrenBulkActionForm, SetChildrenPriceForm = get_classes(
    "dashboard.catalogue.forms",
    ("ChildrenBulkActionForm", "SetChildrenPriceForm"),
)
Product = get_model("catalogue", "Product")
StockRecord = get_model("partner", "StockRecord")


class ChildBulkAction:
    """
    Base class for a bulk action that operates on child products.

    Subclass and set ``label``, and optionally ``form_class``, ``template``,
    and ``context``. Override ``execute`` to implement the action logic.

    ``execute(request, child_ids, form) -> None | HttpResponse``
        Perform the action. Return ``None`` on success or an ``HttpResponse``
        to abort (e.g. re-render the form with an error).

    ``template``
        Should extend ``product_children_bulk_action.html`` and override
        ``{% block extra_column_headers %}``,
        ``{% block extra_column_values %}``, and
        ``{% block action_notice %}`` as needed.
    """

    label = ""
    form_class = ChildrenBulkActionForm
    template = "oscar/dashboard/catalogue/product_children_bulk_action.html"
    context = {}

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
    label = _("Set children price")
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
