from django.db import models
from django.contrib.auth.models import User

class Order(models.Model):
    """
    An order
    """
    customer = models.ForeignKey(User, related_name='orders')
    total_incl_tax = models.FloatField()
    
    
    def __unicode__(self):
        description = "Payment of %.2f from %s" % (self.initial_amount, self.type)
        if self.reference:
            description += " (reference: %s)" % self.reference
        return description

    
#class Batch(models.Model):
#    order = models.ForeignKey('order.Order')
#    partner = models.CharField(max_length=255)
#    delivery_method = models.CharField(max_length=128)
#    # Not all batches are actually delivered (such as downloads)
#    delivery_address = models.ForeignKey('order.Address', null=True, blank=True)
#    # Whether the batch should be dispatched in one go, or as they become available
#    dispatch_option = models.CharField(max_length=128, null=True, blank=True)
#
#
#class BatchLine(models.Model):
#    batch = models.ForeignKey('order.Batch')
    
