from django.db import models
from oscar.payment.abstract_models import AbstractSource, AbstractTransaction

class Source(AbstractSource):
    num_transactions = models.IntegerField(default=0)

class Transaction(AbstractTransaction):
    pass
