import datetime

from django.db import models


class ActiveOfferManager(models.Manager):
    """
    For searching/creating offers within their date range
    """
    def get_query_set(self):
        today = datetime.date.today()
        return super(ActiveOfferManager, self).get_query_set().filter(
            start_date__lte=today, end_date__gte=today)
