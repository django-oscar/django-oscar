from django.db import models

class Item(models.Model):
    pass

class Stock(models.Model):
    product = models.ForeignKey('product.Item')
    price_excl_tax = models.FloatField()
    tax = models.FloatField()
    
    
