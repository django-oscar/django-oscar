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
