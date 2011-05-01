from decimal import Decimal

from django.db import models
from django.utils.translation import ugettext as _


class AbstractOrderTransaction(models.Model):
    
    # Note we don't use a foreign key as the order hasn't been created
    # by the time the transaction takes place
    order_number = models.CharField(max_length=128, db_index=True)
    
    # The 'method' of the transaction - one of 'auth', 'pre', 'cancel', ...
    method = models.CharField(max_length=12)
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    merchant_ref = models.CharField(max_length=128)
    
    # Response fields
    datacash_ref = models.CharField(max_length=128)
    auth_code = models.CharField(max_length=128, blank=True, null=True)
    status = models.PositiveIntegerField()
    reason = models.CharField(max_length=255)
    
    # Store full XML for debugging purposes
    request_xml = models.TextField()
    response_xml = models.TextField()
    
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        abstract = True
