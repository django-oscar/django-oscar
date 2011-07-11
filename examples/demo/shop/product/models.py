from oscar.apps.catalogue.abstract_models import AbstractItem

from django.db import models

class Item(AbstractItem):
    batteries_needed = models.BooleanField(default=False)
    batteries_included = models.BooleanField(default=False)

# We have to import any oscar implementations after we define our own, otherwise Django picks up the wrong one
from oscar.apps.catalogue.models import ItemClass, AttributeType, AttributeValueOption, ProductAttributeValue, Option