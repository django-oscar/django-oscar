"""
Bookshop product models.

We subclass the abstract models from oscar and extend them to model
the domain of bookshops.
"""
from django.db import models
from oscar.product.abstract_models import *
# We reuse the vanilla models from oscar for some models
from oscar.product.models import AttributeValueOption, AttributeType, ItemAttributeValue, ItemClass

class Item(AbstractItem):
    format = models.CharField(max_length=128, default="Paperback")
    isbn = models.CharField(max_length=13)
    contributors = models.ManyToManyField('product.Contributor')
    date_published = models.DateTimeField()


class Contributor(models.Model):
    name = models.CharField(max_length=255)
