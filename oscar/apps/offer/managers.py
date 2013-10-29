from django.utils.timezone import now
from django.db import models


class ActiveOfferManager(models.Manager):
    """
    For searching/creating offers within their date range
    """
    def get_query_set(self):
        cutoff = now()
        return super(ActiveOfferManager, self).get_query_set().filter(
            models.Q(end_datetime__gte=cutoff) | models.Q(end_datetime=None),
            start_datetime__lte=cutoff)

class RangeManager(models.Manager):
    """
    Base Range Manager
    """
    def get_query_set(self):
        return super(RangeManager, self).get_query_set()

class BrowsableRangeManager(models.Manager):
    """
    For searching only ranges which have the "is_browsable" flag set to True.
    """
    def get_query_set(self):
        return super(BrowsableRangeManager, self).get_query_set().filter(is_browsable=True)