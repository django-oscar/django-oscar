"""
Clothes-shop models

We subclass the abstract models from oscar and extend them to model
the domain of bookshops.
"""
from django.db import models
from oscar.product.abstract_models import *
from oscar.product.models import AttributeValueOption, AttributeType, ItemAttributeValue, ItemClass

class AlbumToTracks(models.Model):
    tracks = models.ManyToManyField(Product)