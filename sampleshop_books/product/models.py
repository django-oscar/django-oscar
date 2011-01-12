"""
Bookshop product models
"""
from django.db import models
from oscar.product.abstract_models import *

class ItemType(AbstractItemType):
    pass

class Item(AbstractItem):
    format = models.CharField(max_length=128, default="Paperback")
    isbn = models.CharField(max_length=13)
    contributors = models.ManyToManyField('product.Contributor')
    date_published = models.DateTimeField()

class Contributor(models.Model):
    name = models.CharField(max_length=255)

class AttributeType(AbstractAttributeType):
    pass

class ItemAttributeValue(AbstractItemAttributeValue):
    pass
