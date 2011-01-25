"""
Clothes-shop models

We subclass the abstract models from oscar and extend them to model
the domain of bookshops.
"""
from django.db import models
from oscar.product.abstract_models import AbstractItem

class Item(AbstractItem):
    label = models.CharField(max_length=32, default='Gucci')
    
    def test(self):
        print 'this is the subclass'

# Not quite sure why, but this import statement needs to come after the declaration of the 
# local Item class.  I think it's to do with the lazy loading of relations.        
from oscar.product.models import AttributeValueOption, AttributeType, ItemAttributeValue, ItemClass         
