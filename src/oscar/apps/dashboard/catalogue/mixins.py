from django.contrib import messages
from django.db.models import Q
from django.db.transaction import atomic
from django.shortcuts import redirect
from django.utils.translation import ngettext

from oscar.views.generic import BulkEditMixin


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


class PublicVisibilityUpdateMixin(BulkEditMixin):
    actions = (
        "make_public",
        "make_non_public",
    )

    def make_non_public(self, request, records):
        return self._update_public_flag(records, False)

    def make_public(self, request, records):
        return self._update_public_flag(records, True)

    @atomic
    def _update_public_flag(self, records, value):
        for record in records:
            record.is_public = value
            record.save()
        total_records = len(records)
        messages.info(
            self.request,
            ngettext(
                "Public status was successfully updated for %(count)d record.",
                "Public status was successfully updated for %(count)d records.",
                total_records,
            )
            % {"count": total_records},
        )
        return redirect(self.request.get_full_path())
