from django.db import models

class AbstractItemCustomField(models.Model):
    product = models.OneToOneField('product.Item', null=False)
    field_name = models.CharField(max_length=128)
    field_value = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    
    class Meta:
        abstract = True
        unique_together = ('product', 'field_name')