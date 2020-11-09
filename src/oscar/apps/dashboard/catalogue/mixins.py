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

        return queryset.filter(stockrecords__partner__users__pk=user.pk).distinct()
