from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext as _


class AbstractTransaction(models.Model):
    order_number = models.CharField(max_length=128)
    type = models.CharField(max_length=128)
    transaction_ref = models.CharField(max_length=128)
    merchant_ref = models.CharField(max_length=128)
    amount = models.DecimalField()
    auth_code = models.CharField(max_length=128, blank=True, required=True)
    response_code = models.PositiveIntergerField()
    response_message = models.CharField(max_length=255)
    request_xml = models.TextField()
    response_xml = models.TextField()
    date = models.DateTime()
