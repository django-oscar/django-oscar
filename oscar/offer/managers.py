import datetime

from django.db import models


class ActiveOfferManager(models.Manager):
    u"""
    For searching/creating ACTIVE offers only.
    """
    
    def get_query_set(self):
        today = datetime.date.today()
        return super(ActiveOfferManager, self).get_query_set().filter(start_date__lte=today, end_date__gt=today)

