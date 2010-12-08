from django.db import models

class Item(models.Model):
    title = models.CharField(max_length=255)
    pass


class StockRecord(models.Model):
    product = models.ForeignKey('product.Item')
    price_excl_tax = models.FloatField()
    tax = models.FloatField()
    
    
