# pylint: disable=wildcard-import, unused-wildcard-import
from django.db import models

from oscar.apps.partner import abstract_models


class StockRecord(abstract_models.AbstractStockRecord):
    # Dummy additional field
    offer_name = models.CharField(max_length=128, null=True, blank=True)


from oscar.apps.partner.models import *  # noqa isort:skip
