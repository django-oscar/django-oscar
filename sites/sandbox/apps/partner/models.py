from django.db import models

from oscar.apps.partner import abstract_models


class StockRecord(abstract_models.AbstractStockRecord):
    offer_name = models.CharField(max_length=128, null=True)


from oscar.apps.partner.models import *
