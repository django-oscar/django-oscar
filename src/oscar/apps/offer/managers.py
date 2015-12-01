from django.db import models
from django.utils.timezone import now


class ActiveOfferManager(models.Manager):
    """
    For searching/creating offers within their date range
    """
    def get_queryset(self):
        cutoff = now()
        return super(ActiveOfferManager, self).get_queryset().filter(
            models.Q(end_datetime__gte=cutoff) | models.Q(end_datetime=None),
            start_datetime__lte=cutoff).filter(status=self.model.OPEN)


class BrowsableRangeManager(models.Manager):
    """
    For searching only ranges which have the "is_browsable" flag set to True.
    """
    def get_queryset(self):
        return super(BrowsableRangeManager, self).get_queryset().filter(
            is_public=True)
