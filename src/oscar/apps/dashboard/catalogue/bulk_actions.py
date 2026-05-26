from decimal import Decimal

from django.contrib import messages
from django.db.models import Case, DecimalField, F, Value, When
from django.db.models.functions import Greatest
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
    def execute(self, request, objects):
        if not objects:
            return
        model = type(objects[0])
        count = model.objects.filter(pk__in=[r.pk for r in objects]).update(
            is_public=True
        )
        messages.success(
            request,
            ngettext(
                "Public status was successfully updated for %(count)d record.",
                "Public status was successfully updated for %(count)d objects.",
                count,
            )
            % {"count": count},
        )


class MakeNonPublicAction(BulkAction):
    label = _("Make non-public")

    @atomic
    def execute(self, request, objects):
        if not objects:
            return
        model = type(objects[0])
        count = model.objects.filter(pk__in=[r.pk for r in objects]).update(
            is_public=False
        )
        messages.success(
            request,
            ngettext(
                "Public status was successfully updated for %(count)d record.",
                "Public status was successfully updated for %(count)d objects.",
                count,
            )
            % {"count": count},
        )


class ChildBulkAction(IntermediateBulkAction):
    """Base class for a two-step bulk action that operates on child products."""

    form_class = ChildrenBulkActionForm
    template = "oscar/dashboard/catalogue/product_children_bulk_action.html"

    def filter_children_queryset(self, qs):
        return qs


class MakeChildrenPublicAction(ChildBulkAction):
    label = _("Make variants public")

    @atomic
    def execute(self, request, objects, form):
        count = Product.objects.filter(
            pk__in=[r.pk for r in objects], structure=Product.CHILD
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
    def execute(self, request, objects, form):
        count = Product.objects.filter(
            pk__in=[r.pk for r in objects], structure=Product.CHILD
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

    def filter_children_queryset(self, qs):
        return qs.filter(stockrecords__isnull=False).distinct()

    @atomic
    def execute(self, request, objects, form):
        child_ids = [r.pk for r in objects]
        specific = form.get_specific_prices()
        override_ids = [pk for pk in child_ids if pk in specific]
        rest_ids = [pk for pk in child_ids if pk not in specific]
        partners = form.cleaned_data.get("partners")
        partner_filter = {"partner__in": partners} if partners else {}

        count = 0

        if override_ids:
            count += StockRecord.objects.filter(
                product_id__in=override_ids,
                product__structure=Product.CHILD,
                **partner_filter,
            ).update(
                price=Case(
                    *[
                        When(product_id=pk, then=Value(p))
                        for pk, p in specific.items()
                        if pk in override_ids
                    ],
                    output_field=DecimalField(),
                )
            )

        if rest_ids:
            qs = StockRecord.objects.filter(
                product_id__in=rest_ids,
                product__structure=Product.CHILD,
                **partner_filter,
            )
            base = form.cleaned_data.get("new_price")
            amount = form.cleaned_data.get("increase_by_amount")
            percentage = form.cleaned_data.get("increase_by_percentage")

            if base is not None:
                count += qs.update(price=base)
            elif amount is not None:
                count += qs.update(
                    price=Greatest(F("price") + amount, Value(Decimal("0")))
                )
            elif percentage is not None:
                multiplier = Decimal("1") + percentage / Decimal("100")
                count += qs.update(
                    price=Greatest(F("price") * multiplier, Value(Decimal("0")))
                )

        messages.success(
            request,
            ngettext(
                "Price updated on %(count)d stockrecord.",
                "Price updated on %(count)d stockrecords.",
                count,
            )
            % {"count": count},
        )
